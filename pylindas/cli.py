import argparse
import os
import pandas as pd
import yaml
import logging

from pylindas import Cube
from pylindas.fetch import fetch
from pylindas.example import list_examples, load_example
from pylindas.pycube.shared_dimension import convert_geojson_to_ttl
from pylindas.lindas.paths import safe_path


logger = logging.getLogger('pycube')


def serialize(input_directory: str, output_ttl: str, na_values: list[str], sep: str = ",", decimal: str = "."):
    input_directory = safe_path(input_directory)
    csv_path = safe_path("data.csv", base_dir=input_directory)
    yml_path = safe_path("description.yml", base_dir=input_directory)
    json_path = safe_path("description.json", base_dir=input_directory)

    if os.path.exists(yml_path):
        with open(yml_path) as file:
            cube_yaml = yaml.safe_load(file)
    elif os.path.exists(json_path):
        with open(json_path) as file:
            cube_yaml = yaml.safe_load(file)
    else:
        raise FileNotFoundError("Neither description.yml nor description.json found in the directory")

    df = pd.read_csv(csv_path, na_values=na_values, sep=sep, decimal=decimal)

    cube = Cube(dataframe=df, cube_yaml=cube_yaml, environment="TEST", local=True)
    cube.prepare_data()
    cube.write_cube()
    cube.write_observations()
    cube.write_shape()
    cube.serialize(safe_path(output_ttl))
    print(cube)


def configure_logging(log_level):
    class CustomFormatter(logging.Formatter):
        """Custom logging formatter to add colors based on log level."""

        COLORS = {
            'DEBUG': '\033[0m',  # Normal
            'INFO': '\033[94m',  # Blue
            'WARNING': '\033[93m',  # Yellow
            'ERROR': '\033[91m',  # Red
            'CRITICAL': '\033[91m',  # Red
        }

        def format(self, record):
            log_fmt = self.COLORS.get(record.levelname, '\033[0m') + '%(levelname)s: %(message)s\033[0m'
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    console_handler = logging.StreamHandler()
    logger.setLevel(log_level)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)


def main():
    parser = argparse.ArgumentParser(description="Cube data operations")
    subparsers = parser.add_subparsers(dest="operation", help="Operation to perform")

    serialize_parser = subparsers.add_parser("serialize", help="Serialize cube data")
    serialize_parser.add_argument("input_directory", help="Directory containing the data files")
    serialize_parser.add_argument("output_ttl", help="Output TTL file")
    serialize_parser.add_argument("--na_value", nargs="+", help="Values to treat as NA")
    serialize_parser.add_argument("--sep", default=",", nargs="?", help="Separator for CSV file")
    serialize_parser.add_argument("--decimal", default=".", nargs="?", help="Decimal separator")
    serialize_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    fetch_parser = subparsers.add_parser("fetch", help="Fetches a dataset from a URL")
    fetch_parser.add_argument("input_url", type=str, help="The URL of the dataset to fetch")
    fetch_parser.add_argument("output", type=str, help="The directory to save the output files")
    fetch_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    shared_parser = subparsers.add_parser("shared", help="Shared Dimension operations")
    shared_subparsers = shared_parser.add_subparsers(dest="suboperation", help="Shared sub-operations")

    convert_geojson_parser = shared_subparsers.add_parser("convert_geojson", help="Convert GeoJSON to TTL")
    convert_geojson_parser.add_argument("input_geojson", type=str, help="Input GeoJSON file")
    convert_geojson_parser.add_argument("output_ttl", type=str, help="Output TTL file")
    convert_geojson_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    example_parser = subparsers.add_parser("example", help="Example operations")
    example_subparsers = example_parser.add_subparsers(dest="suboperation", help="Example sub-operations")

    list_parser = example_subparsers.add_parser("list", help="List all examples")
    list_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    start_fuseki_parser = example_subparsers.add_parser("start-fuseki", help="Start a Fuseki database")
    start_fuseki_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    load_parser = example_subparsers.add_parser("load", help="Load an example by name")
    load_parser.add_argument("example_name", type=str, help="The name of the example to load", choices=[example["id"] for example in list_examples()])
    # add optional base_uri argument to load parser
    load_parser.add_argument("--base-uri", type=str, help="The base URI for a SPARQL database (Fuseki supported)", default="http://localhost:3030/dataset")
    load_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    schema_parser = subparsers.add_parser("schema", help="Schema operations")
    schema_subparsers = schema_parser.add_subparsers(dest="suboperation", help="Schema sub-operations")
    import_parser = schema_subparsers.add_parser("import", help="Import the description schema file")
    import_parser.add_argument("output", type=str, help="Output file")
    import_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")


    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose == 1 else logging.INFO

    configure_logging(log_level)

    if args.operation == "serialize":
        serialize(args.input_directory, args.output_ttl, args.na_value, args.sep, args.decimal)
    elif args.operation == "fetch":
        fetch(args.input_url, args.output)
    elif args.operation == "example":
        if args.suboperation == "list":
            examples = list_examples()
            for example in examples:
                print(f'{example["id"]}: {example["name"]}')
        elif args.suboperation == "load":
            load_example(args.example_name, args.base_uri)
        elif args.suboperation == "start-fuseki":
            os.system("scripts/fuseki/start.sh")
    elif args.operation == "shared":
        if args.suboperation == "convert_geojson":
            convert_geojson_to_ttl(args.input_geojson, args.output_ttl)
    elif args.operation == 'schema':
        if args.suboperation == "import":
            description_schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'description.schema.json')
            with open(description_schema_path, 'r') as f:
                schema = f.read()
            output_path = safe_path(args.output)
            with open(output_path, 'w') as f:
                f.write(schema)
                logger.debug(f"Imported description into current directory: {output_path}")



if __name__ == "__main__":
    main()