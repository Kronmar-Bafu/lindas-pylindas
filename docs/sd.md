
# Shared Dimensions

The term `Shared Dimension` refers to a very specific data structure within the [cube.link](https://cube.link) universe.

## Shared Dimensions Queries

To link a dimension to an existing Shared Dimension, the following steps are necessary:

- find a suitable Shared Dimension
- use the URIs of the terms of that Shared Dimension to configure dimension in the yaml file and its "mapping" field

`pylindas` has a basic implementation of:

- basic queries to request shared dimensions information from [LINDAS](https://lindas.admin.ch) (including terms and their URIs)
- display the results, line by line

See the folder `pylindas/shared_dimension_queries` and its [README](../pylindas/shared_dimension_queries/README.md) for detailed explanation

## Generation of Shared Dimensions

`pylindas` has a basic implementation to generate a Shared Dimension by transforming a .csv file to a corresponding RDF.  

See the folder `pylindas/pyshareddimension` and its [README](../pylindas/pyshareddimension/README.md) for detailed explanations.
