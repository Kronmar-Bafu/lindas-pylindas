# pylindas

## About

`pylindas` is a package to build and publish linked data such as cubes as defined by [cube.link](https://cube.link), describing a schema to describe structured data from tables in [RDF](https://www.w3.org/RDF/). It allows for an alternative to the [Cube-Creator](https://cube-creator.lindas.admin.ch). Currently this project is heavily linked to the [LINDAS](lindas.admin.ch) the Swiss Federal Linked Data Service.

For further information, please refer to our [Wiki](https://github.com/Kronmar-Bafu/cubelink/wiki)

## Installation

There are two ways to install this package, locally or through the [Python Package Index (PyPI)](https://pypi.org).

### Locally

Clone this repository and `cd` into the directory. You can now install this package locally on your machine - we advise to use a virtual environment to avoid conflicts with other projects. Additionally, install all dependencies as described in `requirements.txt`

```
pip install -e .
pip install -r requirements.txt
```

### Published Version

You can install this package through pip without cloning the repository.

```
pip install pylindas
```

## Contributing and Suggestions

If you wish to contribute to this project, feel free to clone this repository and open a pull request to be reviewed and merged.

Alternatively feel free to open an issue with a suggestion on what we could implement. We laid out a rough road map for the features ahead on our [Timetable](https://github.com/Kronmar-Bafu/cubelink/wiki/Timetable)

## Functionality and structure

This package consists of multiple sub modules

### `pycube`

To avoid the feeling of a black box, our philosophy is to make the construction of cubes modular. The process will take place in multiple steps, outlined below.

1. **Initialization**

```
from pylindas.pycube import Cube

cube = pycube.Cube(dataframe: pd.Dataframe, cube_yaml: dict, shape_yaml: dict)
```

This step sets some need background information about the cube up.

2. **Mapping**

```
cube.prepare_data()
```

Adds observation URIs and applies the mappings as described in the shape yaml.

3. **Write `cube:Cube`**

```
cube.write_cube()
```

Writes the `cube:Cube`.

4. **Write `cube:Observation`**

```
cube.write_observations()
```

Writes the `cube:Observation`s and the `cube:ObservationSet`. The URI for the observations are written as `<cube_URI/observations/[list_of_key_dimensions]>`. This should avoid the possibilities of conflicts in their uniqueness.

5. **Write `cube:ObersvationConstraint`**

```
cube.write_shape()
```

Writes the `cube:ObservationConstraint`.

### The full work-flow

```
# Write the cube
cube = pycube.Cube(dataframe: pd.DataFrame, cube_yaml: dict, shape_yaml: dict)
cube.prepare_data()
cube.write_cube()
cube.write_observations()
cube.write_shape()

# Upload the cube
cube.upload(endpoint: str, named_graph: str)
```

For an upload, use `cube.upload(endpoint: str, named_graph: str)` with the proper `endpoint` as well as `named_graph`.

A `lindas.ini` file is read for this step, containing these information as well as a password. It contains the structure:

```
[TEST]
endpoint=https://stardog-test.cluster.ldbar.ch
username=a-lindas-user-name
password=something-you-don't-need-to-see;)
```

With additional information for the other environments.

## Command line

If you wish, a command line utility is present, that expects an opinionated way to store
the data and the description in a directory. It then helps you to perform common operations.

### Directory Layout

The directory should be structured as follows:

- `data.csv`: This file contains the observations.
- `description.json` or `description.yml`: This file contains the cube and dimension descriptions.

### Command Line Usage

For example, to serialize the data, use:

```
python cli.py serialize <input_directory> <output_ttl_file>
```

For additional help and options, you can use:

```
python cli.py --help
```

### Fetching from data sources

There is the possibility to download datasets from other data sources. Right now, the functionality is basic, but
it could be possible in the future to extend it.

- It supports only datasets coming from data.europa.eu
- It supports only datasets with a Frictionless datapackage

See [Frictionless](https://frictionlessdata.io/introduction/#why-frictionless) for more information on Frictionless.

```
python fetch.py 'https://data.europa.eu/data/datasets/fc49eebf-3750-4c9c-a29e-6696eb644362?locale=en' example/corona/
```

### Examples

Multiple cube example are ready in the `example` directory.

```bash
$ python cli.py example list
corona: Corona Numbers Timeline
kita: Number of kids in day care facilities
wind: Wind turbines — operated WKA per year in Schleswig-Holstein
```

To load an example in a Fuseki database, you can use the load subcommand of the example command.

```bash
$ python cli.py example load kita
```

There is a `start-fuseki` command that can be used to start a Fuseki server containing data
from the examples.

```bash
$ python cli.py example start-fuseki
```

## About shared dimensions queries
When a data scientist wants to link a dimension to an existing Shared Dimension, he has to:
- Find a suitable Shared Dimension 
- Use the URLs of the terms of that Shared Dimension to configure dimension in the yml file and its "mapping" field

This is a first implementation of:
- Basic queries to request shared dimensions information from LINDAS (including terms and their URLs)
- Display the results, line by line

See the folder `pylindas/shared_dimension_queries` and its [README](pylindas/shared_dimension_queries/README.md) for detailed explanation

Shared dimensions work only in Python >=3.11

About generating Shared Dimension, see here under.

## About concept tables and multi-lingual concepts
This is first implementation to handle:
- concept tables
- multilingual concepts

A concept table is the possibility to handle the values of a dimension as a url to a new resource (a concept).  
This is similar to an object that is the URL of a Shared Dimension's term, but here the concepts are created for the cube and uploaded with the cube.  
Remark: if the resource/concept already exist, than the case is similar to the handling of Shared Dimensions mapping, and this is already handled by pyCube with the "mapping" mechanism. 

See the folder `example/Cubes/concept_table_airport` and its [README](example/Cubes/concept_table_airport/README.md) for detailed explanation

## About generation of shared dimensions
This is a first implementation to generate a shared dimension, following an approach similar to pyCube, but to transform a .csv file to the corresponding RDF.  

See the folder `pylindas/pyshareddimension` and its [README](pylindas/pyshareddimension/README.md) for detailed explanation

Shared dimensions work only in Python >=3.11


