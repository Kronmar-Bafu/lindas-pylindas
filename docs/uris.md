# URIs

It is important to understand, how the settings in the `description.yaml` file determine the different URIs of the cube:

For the following settings:

```yaml
Base-URI: https://environment.ld.admin.ch/foen/
Identifier: wps
Version: 1
```

the following URIs will result:

- Cube: https://environment.ld.admin.ch/foen/cube/wps/1
- Observation Set: https://environment.ld.admin.ch/foen/cube/wps/1/ObservationSet
- Observation Constraints: https://environment.ld.admin.ch/foen/cube/wps/1/shape
- Observations: https://environment.ld.admin.ch/foen/cube/wps/1/observation/{list_of_key_dimensions}
- Properties: https://environment.ld.admin.ch/foen/{propertyName}