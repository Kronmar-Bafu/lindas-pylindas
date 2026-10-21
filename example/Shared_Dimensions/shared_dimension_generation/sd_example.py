#!/usr/bin/env python

import pandas as pd
import yaml
import os

from pylindas.pyshareddimension import SharedDimension

BASEDIR = os.path.dirname(__file__)
DIMENSIONFILE = os.path.join(BASEDIR, "sd_terms.csv")
CONFIGFILE = os.path.join(BASEDIR, "sd_description.yml")
SDFILE = os.path.join(BASEDIR, "sd_example.ttl")
SHACLFILE = os.path.join(BASEDIR, "sd_example_Shacl_result.ttl")
SHAREDDIMENSIONSHAPE = "https://raw.githubusercontent.com/Kronmar-Bafu/lindas-pylindas/refs/heads/main/pylindas/pyshareddimension/shared_dimension_shape.ttl"

terms_df = pd.read_csv(DIMENSIONFILE, encoding="utf8", sep=";")

with open(CONFIGFILE) as file:
    sd_yaml = yaml.safe_load(file)

sd = SharedDimension(dataframe=terms_df, sd_yaml=sd_yaml, environment="TEST", local=True)
sd.prepare_data()
sd.write_sd()
sd.write_terms()
sd.serialize(SDFILE)
print(sd)

# About the SHACL validation, please see the comment of the SharedDimension.validate() method
#   in order to understand the parameters
# This is work in progress as the SHACL file has to be passed as parameter instead of being downloaded from the Web behind the scene
resultBool, resultTxt = sd.validate(SHAREDDIMENSIONSHAPE, SHACLFILE)
print(f"Shared dimension validation result: {resultBool}, with message '{resultTxt}'")
