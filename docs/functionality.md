# Basic Functionality and Structure

The `pylindas` package consists of multiple sub modules:

## `pycube`

To avoid the feeling of a black box, the philosophy of `pycube` is to make the construction of cubes modular. The process will take place in multiple steps, outlined below:

1. **Initialization**

```python
from pylindas.pycube import Cube

cube = pycube.Cube(dataframe: pd.Dataframe, cube_yaml: dict)
```

This step initializes the cube with the data (`dataframe`) and the configuration (`cube_yaml`).

2. **Mapping**

```python
cube.prepare_data()
```

Creates the observation URIs and applies the mappings as described in the `cube_yaml`.

3. **Write `cube:Cube`**

```python
cube.write_cube()
```

Writes the `cube:Cube`.

4. **Write `cube:Observation`**

```python
cube.write_observations()
```

Writes the `cube:Observation`s and the `cube:ObservationSet`.

5. **Write `cube:ObersvationConstraint`**

```python
cube.write_shape()
```

Writes the `cube:ObservationConstraint`.

## The Complete Work-Flow

```python
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