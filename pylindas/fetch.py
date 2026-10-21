"""
Utils to download a data.europa.eu dataset with frictionless metadata,
and generate a description.json.

TODO: Make it  more agnostic from data.europa.eu
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from jsonschema import Draft202012Validator

from pylindas.lindas.paths import safe_path

import logging

logger = logging.getLogger('pycube')

def download_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def read_schema(schema_path):
    with open(schema_path, 'r') as f:
        return json.load(f)

class DataEuropaFetcher(object):
    """
    In the future, the class should be splitted into frictionless parsing methods and
    data.europa.eu fetch methods.
    """
    def __init__(self):
        pass

    def _transform_url(self, input_url):
        dataset_id = input_url.split('/')[-1].split('?')[0]
        return f"https://data.europa.eu/api/hub/search/datasets/{dataset_id}"


    def _extract_metadata(self, data):
        metadata = {
            "title": {
                "en": data['result']['title'].get('en', ''),
                "de": data['result']['title'].get('de', '')
            },
            "description": {
                "en": data['result']['description'].get('en', ''),
                "de": data['result']['description'].get('de', '')
            },
            "publisher": data['result'].get('publisher', '')
        }
        return metadata


    def _get_distributions(self, distributions):
        csv_data = None
        frictionless_data = None
        for distribution in distributions:
            if distribution['title'].get('en') == "Frictionless Tabular Data Resource":
                frictionless_url = distribution['access_url'][0]
                frictionless_data = requests.get(frictionless_url).json()
            if distribution['format'].get('id') == "CSV":
                csv_url = distribution['access_url'][0]
                csv_data = requests.get(csv_url).content
        return {
            "frictionless": frictionless_data,
            "csv": csv_data
        }


    def _infer_dimension_type(self, field: Dict[Any, Any], primary_keys: List[str]) -> str:
        """Infer the dimension type based on field properties."""
        if field['name'] in primary_keys:
            return "Key Dimension"
        return "Measure Dimension"


    def _infer_scale_type(self, field: Dict[Any, Any]) -> str:
        """Infer the scale type based on field properties."""
        field_type = field.get("type")
        if field_type == "string":
            return "nominal"
        elif field_type == "integer":
            return "interval"
        elif field_type == "number":
            return "ratio"
        return "nominal"  # default


    def _infer_temporal_dimension(self, field: Dict[Any, Any]) -> bool:
        """Infer if the field is a temporal dimension."""
        field_type = field.get("type")
        if field_type == "date":
            return True
        if field_type == "time":
            return True
        field_name = field['name']
        if field_name.lower() in ["jahr", "year", "date", "datum"]:
            logger.warning(f'Dimension {field_name}: Temporal dimension inferred from field name. Please verify.')
            return True



    def _generate_dimensions(self, data_metadata: Dict[Any, Any]) -> Dict[str, Dict[Any, Any]]:
        """Generate dimensions from data metadata schema."""
        dimensions = {}
        
        primary_key = data_metadata["schema"].get('primaryKey', [])
        primary_keys = primary_key if isinstance(primary_key, list) else [primary_key]
        if not primary_keys:
            first_field = data_metadata["schema"]["fields"][0]["name"]
            logger.warning(f"Primary key not found in schema. Using first field {first_field} as primary key. You may need to adjust Key/Measure Dimension manually.")
            primary_key = first_field

        for field in data_metadata["schema"]["fields"]:
            field_name = field["name"]
            
            # Create dimension object
            dimension = {
                "name": {
                    "de": field.get("title", field_name),
                    "en": field.get("title", field_name)
                },
                "dimension-type": self._infer_dimension_type(field, primary_keys),
                "scale-type": self._infer_scale_type(field),
                "path": field_name,
                "description": {
                    "de": field.get("description", f"Beschreibung für {field_name}"),
                    "en": field.get("description", f"Description for {field_name}")
                }
            }
            
            # Add unit if present
            if "unit" in field:
                dimension["unit"] = field["unit"]
            
            # Add data-kind if temporal
            if self._infer_temporal_dimension(field):
                dimension["data-kind"] = {
                    "type": "temporal",
                    "unit": "year"
                }
                
            dimensions[field_name] = dimension
        
        return dimensions


    def _transform_metadata(self, metadata: Dict[Any, Any], data_metadata: Dict[Any, Any]) -> Dict[Any, Any]:
        """Transform metadata to conform to the JSON schema."""
        
        output = {
            "Name": {
                "de": metadata["title"]["de"],
                "en": metadata["title"]["en"]
            },
            "Description": {
                "de": metadata["description"]["de"],
                "en": metadata["description"]["en"]
            },
            "Publisher": [
                {
                    "IRI": metadata["publisher"]["resource"]
                }
            ],
            "Creator": [
                {
                    "IRI": metadata["publisher"]["resource"]
                }
            ],

            "Contributor": [],

            "Date Created": datetime.now().isoformat(),
            "Contact Point": {
                "E-Mail": "opendata@example.ch",  # Example email
                "Name": metadata["publisher"]["name"]
            },
            "Base-URI": data_metadata["path"],
            "Identifier": data_metadata["name"],
            "Version": 0.1,
            "Work Status": "Draft",
            "Visualize": True,
            "Accrual Periodicity": "",
            "Namespace": "https://opendata.example.ch",
            "dimensions": self._generate_dimensions(data_metadata)
        }
        
        return output


    def fetch_dataset(self, input_url, output_dir):
        transformed_url = self._transform_url(input_url)
        data = download_json(transformed_url)

        metadata = self._extract_metadata(data)

        safe_output_dir = safe_path(output_dir) if output_dir else os.getcwd()
        data_csv_filename = safe_path('data.csv', base_dir=safe_output_dir)
        description_json_filename = safe_path('description.json', base_dir=safe_output_dir)
        frictionless_json_filename = safe_path('frictionless.json', base_dir=safe_output_dir)

        distributions = self._get_distributions(data['result']['distributions'])

        logger.info(f"Writing {data_csv_filename}")
        with open(data_csv_filename, 'wb') as f:
            f.write(distributions['csv'])

        logger.info(f"Writing {frictionless_json_filename}")
        with open(frictionless_json_filename, 'w') as f:
            f.write(json.dumps(distributions['frictionless'], indent=2))

        current_file_dir = os.path.dirname(os.path.realpath(__file__))
        description_schema_path = os.path.join(current_file_dir, 'description.schema.json')
        description_schema = read_schema(description_schema_path)
        description = self._transform_metadata(metadata, distributions['frictionless'])
        schema_path = os.path.relpath(
            description_schema_path,
            start=safe_output_dir
        )
        description = {
            "$schema": f"{schema_path}",
            **description
        }
        logger.info(f"Writing {description_json_filename}")
        with open(description_json_filename, 'w') as f:
            f.write(json.dumps(description, indent=2))
        
        validator = Draft202012Validator(description_schema)
        errors = list(validator.iter_errors(description))
        for error in errors:
            logger.warning(f"Validation Error: {error.message}")

        serialize_command = f"""# You may want to adjust the command with --sep and --decimal, depending on the data.csv
python cli.py serialize {output_dir} {os.path.join(output_dir, 'cube.ttl')}"""
        if len(errors):
            logger.warning(f"""The data and description have been downloaded. There were validation errors during description validation, you should fix them before running the following command

{serialize_command}
""")
        else:
            logger.info(f"""Success ! The data and description have been downloaded, you may now verify it, adjust it, and then run serialize to create RDF triples

{serialize_command}
""")


def fetch(input_url: str, output_dir: str):
    # create the output dir if it does not exist, validating it stays within cwd
    if output_dir:
        output_dir = safe_path(output_dir)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

    if input_url.startswith('https://data.europa.eu'):
        fetcher = DataEuropaFetcher()
        fetcher.fetch_dataset(input_url, output_dir)
    else:
        raise ValueError('Only supporting datasets from data.europa.eu at the moment, make sure your input URL starts with https://data.europa.eu')