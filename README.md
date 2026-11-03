# pylindas

## About

`pylindas` is a python package for building and publishing linked data cubes according to the [cube.link](https://cube.link) schema. This schema is used to transform tabular data into [RDF](https://www.w3.org/RDF/). `pylindas` is an alternative to the [Cube-Creator](https://cube-creator.lindas.admin.ch). Whereas the Cube-Creator is a [GUI](https://en.wikipedia.org/wiki/Graphical_user_interface) tool, `pylindas` is more suited to fit into a pipeline workflow to create RDF. Currently this project is heavily linked to [LINDAS](https://lindas.admin.ch) the Swiss Federal Linked Data Service.

## Getting started

New to `pylindas`? The best starting point is the showcase notebook
[`example/Cubes/example.ipynb`](example/Cubes/example.ipynb). It builds a small
`cube.link` cube end to end — load data, describe it, write the cube,
observations and shape, serialize to Turtle, and optionally validate and
upload — and explains each part of the cube schema along the way.

## Documentation

- [Installation](docs/installation.md)
- [Contributing](docs/contributing.md)
- [Basic functionality](docs/functionality.md)
- [Command line usage](docs/cli.md)
- [Examples](docs/examples.md)
- [URIs](docs/uris.md)
- [Concepts](docs/concepts.md)
- [Shared Dimensions](docs/sd.md)
