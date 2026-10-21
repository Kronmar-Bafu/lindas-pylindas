#!/usr/bin/env python

import pandas as pd
import yaml
import os

from pylindas.pycube import Cube
from pylindas.lindas.upload import upload_ttl

BASEDIR = os.path.dirname(__file__)
DATAFILE = os.path.join(BASEDIR, "data.csv")
CONFIGFILE = os.path.join(BASEDIR, "description.yml")
CUBEFILE = os.path.join(BASEDIR, "cube.ttl")

data = pd.read_csv(DATAFILE, encoding="utf-8", sep=",")
with open(CONFIGFILE, encoding="utf-8") as file:
    config = yaml.safe_load(file)

cube = Cube(dataframe=data, cube_yaml=config, environment="TEST", local=True)
cube.prepare_data()
cube.write_cube()
cube.write_observations()
cube.write_shape()
valid, text = cube.validate()
if valid:
    print(text)
    cube.serialize(CUBEFILE)
    if os.path.isfile("lindas.ini"):
        upload_ttl(filename=CUBEFILE, db_file="lindas.ini", environment="TEST", graph_uri="")
else:
    print(text)
    #check for exception in .validate
    raise ValueError("Cube not Valid")