#!/usr/bin/env python

import pandas as pd
import yaml
import os

from pylindas.lindas.namespaces import SCHEMA
from pylindas.pycube import Cube

"""
Author: Fabian Cretton - HEVS

See the description in the README.

This example script only generates the .ttl file, the upload operations are not performed
"""

BASEDIR = os.path.dirname(__file__)
CONFIGFILE = os.path.join(BASEDIR, "description.yml")
CUBEFILE = os.path.join(BASEDIR, "cube.ttl")


# data.csv contains an airport type identifier that doesn't exist in airportconcept.csv
# the goal is to demonstrate that the  check_dimension_object_property() called here under will detect that
DATADUMMY = os.path.join(BASEDIR, "data.csv")
data_df = pd.read_csv(DATADUMMY)

with open(CONFIGFILE) as file:
    config = yaml.safe_load(file)

cube = Cube(dataframe=data_df, cube_yaml=config, environment="TEST", local=True)
cube.prepare_data()
cube.write_cube()
cube.write_observations()
cube.write_shape()

# Add the concept data
# The concept must be defined in the cube_yaml file, as a nested key under the "Concepts" key
#   "typeOfAirport" is the name of that nested key
AIRPORTDATA = os.path.join(BASEDIR, "airportconcept.csv")
airport_concept_df = pd.read_csv(AIRPORTDATA)
cube.write_concept("typeOfAirport", airport_concept_df)

# Check that all the generated URLs for the typeOfAirport are resources (concept) with a SCHEMA.name triple
# This allows to check if all the entries in data.csv correspond to an entry in airportconcept.csv 
# This check should identify the error of the 'dummy' airport type
allConceptsFound = cube.check_dimension_object_property("typeOfAirport", SCHEMA.name)

if not allConceptsFound:
    print("""\nCheck result - WARNING: It seems that some objects of the \"typeOfAirport\" dimension have no matching concept.
          See the log for details and check your data + cube dimension and concepts configuration""")
else:
    print("\nCheck result - SUCCESS: It seems that all objects of the \"typeOfAirport\" dimension have a matching concept.")

cube.serialize(CUBEFILE)

# Just for testing the functionality: add the 'dummy' airport type
AIRPORTDUMMYDATA = os.path.join(BASEDIR, "airportdummyconcept.csv")
airport_concept_dummy_df = pd.read_csv(AIRPORTDUMMYDATA)
cube.write_concept("typeOfAirport", airport_concept_dummy_df)
allConceptsFound = cube.check_dimension_object_property("typeOfAirport", SCHEMA.name)

if not allConceptsFound:
    print("""\nCheck result - WARNING: It seems that some objects of the \"typeOfAirport\" dimension have no matching concept.
          See the log for details and check your data + cube dimension and concepts configuration""")
else:
    print("\nCheck result - SUCCESS: It seems that all objects of the \"typeOfAirport\" dimension have a matching concept.")

print(cube)


