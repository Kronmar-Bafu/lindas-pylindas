import re
from urllib.parse import quote
from rdflib import BNode, Graph, Literal, RDF, URIRef, XSD
from rdflib.collection import Collection
from datetime import datetime, timezone
from typing import Self
import pandas as pd
import numbers
import sys

from pylindas.lindas.namespaces import *
from pylindas.lindas.query import query_lindas

class SharedDimension:
    _sd_uri: URIRef # Note: Shared Dimension usually do not have a trailing "/" in there URL
    _sd_dict: dict
    _graph: Graph
    _dataframe: pd.DataFrame
    _shape_dict: dict
    _shape_URI: URIRef
    _languages = ["fr", "en", "de", "it"]
    
    def __init__(self, dataframe: pd.DataFrame, sd_yaml: dict, environment: str, local=False):
        """
        Initialize a Shared Dimension (SD) object.

        Args:
            dataframe (pd.DataFrame): The Pandas DataFrame representing the shared dimension terms data.
            sd_yaml (dict): A dictionary containing SD information.
            environment (str): The environment of the SD.
            local (bool): A flag indicating whether the SD is local.

        Returns:
            None
        """
        self._dataframe = dataframe
        self._setup_sd_dict(sd_yaml=sd_yaml,local=local, environment=environment)
        assert self._sd_uri is not None
        self._graph = self._setup_graph()

    def __str__(self) -> str:
        """
        Return a string representation of the SD object.

        This method returns a string representation of the SD object, including its URI and name.

        Returns:
            str: A string representation of the SD object.
        """
        how_many_triples_query = (
            "SELECT (COUNT(*) as ?Triples)"
            "WHERE {"
            "    ?s ?p ?o."
            "}"
        )
        how_many_triples = self._graph.query(how_many_triples_query).bindings[0].get("Triples").value
        output = (f"SD Object <{self._sd_uri}> with name '{self._sd_dict.get('Name').get('en')}'.\n\n"
                  f"{self._dataframe.head()}\n"
                  f"Number of triples in Graph: {how_many_triples}")
        return output

    def prepare_data(self) -> Self:
        """
        Prepare the cube data by constructing terms URIs and applying mappings.
        Also handling the parent term if defined in the configuration.

        This method constructs terms/parents URIs for each row in the dataframe and applies mappings to the dataframe.

        Returns:
            self
        """
        self._construct_terms_uri()

        terms = self._sd_dict.get("Terms")
        if "parent-field" in terms:
            self._construct_parent_uri(terms.get("parent-field"))

        return self

    def write_sd(self) -> Self:
        """
        Write the SD metadata to the graph.

        Returns:
            self
        """
        self._graph.add((self._sd_uri, RDF.type, META.SharedDimension))
        self._graph.add((self._sd_uri, RDF.type, SCHEMA.DefinedTermSet))
        # self._graph.add((self._sd_uri, RDF.type, SKOS.ConceptScheme))

        self._graph.add((self._sd_uri, SCHEMA.identifier, Literal(self._sd_dict.get("Identifier"))))

        names = self._sd_dict.get("Name")
        for lan, name in names.items():
            self._graph.add((self._sd_uri, SCHEMA.name, Literal(name, lang=lan)))
            self._graph.add((self._sd_uri, DCT.title, Literal(name, lang=lan)))

        descriptions = self._sd_dict.get("Description")
        if descriptions:
            for lan, desc in descriptions.items():
                self._graph.add((self._sd_uri, SCHEMA.description, Literal(desc, lang=lan)))

        validFrom = self._sd_dict.get("Valid-from")
        if validFrom:
            self._graph.add((self._sd_uri, SCHEMA.validFrom, Literal(validFrom, datatype=XSD.dateTime)))

        contributor = self._sd_dict.get("Contributor")
        if contributor:
            contributor_node = self._write_contributor(contributor)
            self._graph.add((self._sd_uri, DCT.contributor, contributor_node))

        shacl_node = self._write_shacl()
        self._graph.add((self._sd_uri, SH.property, shacl_node))

        return self

    def get_iri(self) -> URIRef:
        return self._sd_uri

    def _setup_sd_dict(self, sd_yaml: dict, local: bool, environment="TEST") -> None:
        """
        Set up the SD uri + dictionary with the provided YAML data.

        Args:
            sd_yaml (dict): A dictionary containing SD information.

        Returns:
            None
        """
        # Note: Shared Dimension usually do not have a trailing "/" in there URL
        sd_uri = URIRef("https://ld.admin.ch/cube/dimension/" + sd_yaml.get("Identifier"))

        if not local:
            query = f"ASK {{ <{sd_uri}> ?p ?o}}"
            if query_lindas(query, environment=environment) == True:
                sys.exit("Shared Dimension already exists! Please update your yaml")

        self._sd_dict = sd_yaml
        self._sd_uri = URIRef(sd_uri)

    def _setup_graph(self) -> Graph:
        """Set up the graph by binding namespaces and returning the graph object.
        
        Returns:
            Graph: The graph object with namespaces bound.
        """
        graph = Graph()
        for prefix, nmspc in Namespaces.items():
            graph.bind(prefix=prefix, namespace=nmspc)

        return graph

    def _construct_terms_uri(self) -> None:
        """Construct terms URIs for each row in the dataframe.
        
        This function constructs terms URIs for each row in the dataframe based on the SD URI and terms identifier.
        
        Returns:
            None
        """
        termIdentifierField = self._sd_dict.get("Terms").get("identifier-field")

        # Note: Shared Dimension usually do not have a trailing "/" in there URL
        #   -> add it 
        def make_iri(row):
            return self._sd_uri + "/" + quote(row[termIdentifierField])
        self._dataframe['terms-uri'] = self._dataframe.apply(
            make_iri, axis=1
        )
        self._dataframe['terms-uri'] = self._dataframe['terms-uri'].map(URIRef)
        self._dataframe = self._dataframe.set_index("terms-uri")

    def _construct_parent_uri(self, parentField) -> None:
        """Construct parent URIs for each row in the dataframe.
        
        Note: the parentField is the field, in the data, that contains the parent ID from which to build a term's URI
        IMPORTANT: this parentField could be empty, which is the case for the root node

        Returns:
            None
        """
        # Note: Shared Dimension usually do not have a trailing "/" in there URL
        #   -> add it 
        def make_iri(row):
            if not pd.isna(row[parentField]):
                return URIRef(self._sd_uri + "/" + quote(row[parentField]))
        self._dataframe['parent-uri'] = self._dataframe.apply(
            make_iri, axis=1
        )

    def _write_contributor(self, contributor_dict: dict) -> BNode:
        """Writes a contributor to the graph.
        
            Args:
                contact_dict (dict): A dictionary containing information about the contributor: name and email.
                
            Returns:
                BNode or URIRef: The created BNode representing the contributor
        """

        contributor_node = BNode()
        self._graph.add((contributor_node, SCHEMA.email, Literal(contributor_dict.get("email"), datatype=XSD.string)))
        self._graph.add((contributor_node, SCHEMA.name, Literal(contributor_dict.get("name"), datatype=XSD.string)))
        return contributor_node

    def _write_shacl(self) -> BNode:
        """Writes the shacl meta-data to the graph.
            they are used by the Cube Creator when a SD is linked to a dimension of a cube and are the following triples:
			    shacl:property [ schema:name "Anhängevorrichtung"@de,
			 				"Tow coupling"@en,
			 				"Dispositif d’attelage"@fr,
			 				"Dispositivo d’aggancio rimorchio"@it ;
			 			qudt:scaleType <http://qudt.org/schema/qudt/Nominal> ] .            

            Returns:
                BNode or URIRef: The created BNode representing the shacl meta-data
        """

        shacl_node = BNode()

        names = self._sd_dict.get("Name")
        for lan, name in names.items():
            self._graph.add((shacl_node, SCHEMA.name, Literal(name, lang=lan)))

        self._graph.add((shacl_node, QUDT.scaleType, QUDT.Nominal))

        return shacl_node
    
    def write_terms(self) -> Self:
        """Write the terms of the SD

        This function iterates over the rows in the dataframe and adds each row as a term

        Returns:
            Self
        """
        terms = self._sd_dict.get("Terms")
        termIdentifierField = terms.get("identifier-field")
        termNameField= terms.get("name-field")
        multilingual= terms.get("multilingual")
        # Read the valid-from value from the configuration file, as a validFrom information will be added to each term
        validFrom = self._sd_dict.get("Valid-from")
            
        # TODO: optional-field handling: which is currently based on the handling  proposed for the "concepts" (in the respective branch)
        #   After the final decisions are taken about the "concepts" handling, apply it here
        # Prepare the optional fields of the term:
        # - the key of the entry (under the other-fields entry) being the name of the field in the data
        # - handle the URI field if it starts with a "/": adding the sd URI + the defined relative path
        if "other-fields" in terms:
            otherFields = terms.get("other-fields")

            # Note: Shared Dimension usually do not have a trailing "/" in there URL
            #   and the URI field will start with a "/" if it is a relative path
            sdUri =  str(self._sd_uri)
            
            otherFields_dict = {
                key: {
                    **value, 
                    "URI": sdUri + value["URI"] if value["URI"].startswith("/") else value["URI"]
                }
                for key, value in otherFields.items()
            }            
        else:
            otherFields_dict = {}


        self._dataframe.apply(self._add_term, axis=1,  args=(termIdentifierField, termNameField, multilingual, validFrom, otherFields_dict))
        return self

    def _add_term(self, termsData: pd.DataFrame, termIdentifierField: str, termNameField: str, multilingual: bool, validFrom, otherFields_dict) -> None:
        """Add an observation to the cube.
        
            Args:
                termsData (pd.DataFrame): The terms data to be added
                termIdentifierField: the name of the field for the term's identifier
                termNameField: the name of the field for the term's name
                multilingual: is it a multilingual value

        
            Returns:
                None
        """
        # It seems that after _construct_terms_uri() calls _dataframe.set_index("terms-uri"), the term uri is accessible through the .name value
        self._graph.add((termsData.name, RDF.type, SCHEMA.DefinedTerm))
        self._graph.add((termsData.name, RDF.type, SD_MD.SharedDimensionTerm))

        # Add the link to the SD
        self._graph.add((termsData.name, SCHEMA.inDefinedTermSet, self._sd_uri))
        # Seems optional: add the link from the SD to the term
        self._graph.add((self._sd_uri, SCHEMA.hasDefinedTerm, termsData.name))

        self._graph.add((termsData.name, SCHEMA.identifier, Literal(termsData.get(termIdentifierField))))
        
        if multilingual:
            for lang in self._languages:
                name_key = f"{termNameField}_{lang}"
                if name_key in termsData:
                    self._graph.add((termsData.name, URIRef(SCHEMA.name), Literal(termsData.get(name_key), lang=lang)))            
        else:
            self._graph.add((termsData.name, URIRef(SCHEMA.name), Literal(termsData.get(termNameField))))

        if validFrom:
            self._graph.add((termsData.name, SCHEMA.validFrom, Literal(validFrom, datatype=XSD.dateTime)))

        # Handling parent field
        # If terms have a parent field, a 'parent-uri' was prepared in the dataset (see prepareData())
        if 'parent-uri' in termsData:
            parentURL = termsData.get('parent-uri')
            if parentURL:
                self._graph.add((termsData.name, SKOS.broader, parentURL))

        # Handling other fields/properties
        for key, value in otherFields_dict.items():
            if "multilingual" in value and value['multilingual']:
                for lang in self._languages:
                    key_lng = f"{key}_{lang}"
                    if key_lng in termsData:
                        self._graph.add((termsData.name, URIRef(value['URI']), Literal(termsData.get(key_lng), lang=lang)))
            else:
                if key in termsData:
                    rawValue = termsData.get(key)
                    if not pd.isna(rawValue):
                        sanitized_value = self._sanitize_value(rawValue)
                        self._graph.add((termsData.name, URIRef(value['URI']), sanitized_value))

        # for column in terms.keys():
        #     path = URIRef(self._base_uri + self._get_shape_column(column).get("path"))
        #     sanitized_value = self._sanitize_value(terms.get(column))
        #     self._graph.add((terms.name, URIRef(path), sanitized_value))

    def serialize(self, filename: str) -> Self:
        """Serialize the cube to a file.

        This function serializes the cube to the given file name in turtle format.

        Args:
            filename (str): The name of the file to write the cube to.

        Returns:
            Self
        """
        self._graph.serialize(destination=filename, format="turtle", encoding="utf-8")
        return self
    
    @staticmethod
    def _sanitize_value(value) -> Literal|URIRef:
        """Sanitize the input value to ensure it is in a valid format.
        
            Args:
                value: The value to be sanitized.
        
            Returns:
                Literal or URIRef: The sanitized value in the form of a Literal or URIRef.
        """
        if isinstance(value, numbers.Number):
            if pd.isna(value):
                return Literal("", datatype=CUBE.Undefined)
            else:
                return Literal(value, datatype=XSD.decimal)
        elif isinstance(value, URIRef):
            return value
        else:
            return Literal(str(value))



