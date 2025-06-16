import pandas as pd
import yaml
import os

from pylindas.pycube import Cube
from pylindas.lindas.namespaces import SCHEMA

ENVIRONMENT = os.getenv("CI_ENVIRONMENT_NAME")

# Load data and yaml
df = pd.read_csv("3_data_preparation/data.csv", encoding="utf-8", sep=",")
with open("4_data_integration/integration.yaml", encoding="utf-8") as file:
    cube_yaml = yaml.safe_load(file)

cube = Cube(dataframe=df, cube_yaml=cube_yaml, environment="TEST", local=True)

cube.prepare_data()
cube.write_cube()
cube.write_observations()
cube.write_shape()

# Create concept
age_group_concept = pd.read_csv("3_data_preparation/age.csv", encoding="utf-8", sep=",")
cube.write_concept("age-group", age_group_concept)

cube.serialize("4_data_integration/cube.ttl")