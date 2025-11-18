# Command line

There is also a `pylindas` command line utility, that expects an opinionated way to store
the data and the description in a directory. It then is able to perform common operations.

## Necessary Directory Layout

The directory must be structured as follows:

- `data.csv`: This file contains the observations.
- `description.json` or `description.yml`: This file contains the cube and dimension descriptions.

## Command Line Usage

For example, to serialize the data, use:

```
python cli.py serialize <input_directory> <output_ttl_file>
```

For additional help and options, you can use:

```
python cli.py --help
```

## Fetching from data sources

There is the possibility to download datasets from other data sources. Right now, the functionality is basic, but
it could be possible in the future to extend it.

- It supports only datasets coming from data.europa.eu
- It supports only datasets with a Frictionless datapackage

See [Frictionless](https://frictionlessdata.io/introduction/#why-frictionless) for more information on Frictionless.

```
python fetch.py 'https://data.europa.eu/data/datasets/fc49eebf-3750-4c9c-a29e-6696eb644362?locale=en' example/corona/
```

## CLI Examples

Multiple cube examples are ready in the [example](../example) directory.

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
