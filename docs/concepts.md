# Concepts

The term `concept` refers to a very specific data structure within the [cube.link](https://cube.link) universe.

## Multi-Lingual Concepts

`pylindas` has a basic implementation to handle:

- concept tables
- multilingual concepts

A concept table is the possibility to handle the values of a dimension as a URI to a new resource (a concept). This is similar to an object that is the URI of a Shared Dimension's term, but here the concepts are created for the cube and uploaded with the cube.  

Remark: if the resource/concept already exists, then the case is similar to handling of a Shared Dimensions mapping, and this is already handled by `pylindas` with the "mapping" mechanism.

See the folder `example/Cubes/concept_table_airport` and its [README](../example/Cubes/concept_table_airport/README.md) for detailed explanations.
