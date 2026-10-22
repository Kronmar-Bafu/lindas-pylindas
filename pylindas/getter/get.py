import sparql_dataframe
from SPARQLWrapper import SPARQLWrapper, JSON


def get_cube(endpoint: str, identifier: str, version: str):
    """Retrieve the cube URI based on the provided identifier and version using SPARQL query.
    
        Args:
            endpoint (str): The SPARQL endpoint URL.
            identifier (str): The identifier of the cube.
            version (str): The version of the cube.
    
        Returns:
            str: The URI of the cube.
    
        Raises:
            Exception: If an error occurs during the SPARQL query execution.
    """
    match endpoint:
        case "TEST":
            endpoint = "https://test.lindas.admin.ch/query"
        case "INT":
            endpoint = "https://int.lindas.admin.ch/query"
        case "PROD":
            endpoint = "https://lindas.admin.ch/query"

    query = f"""
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX cube: <https://cube.link/>
        PREFIX schema: <http://schema.org/>

        SELECT ?cube 
        {{
           ?cube a cube:Cube ;
               dcterms:identifier "{identifier}" ;
               schema:version {version} .
        }}
    """
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)

    try:
        resp = sparql.queryAndConvert()

        return resp["results"]["bindings"][0]["cube"]["value"]
    except Exception as e:
        return e


def get_observations(endpoint: str, identifier: str, version: str):
    """Retrieve observations from a given endpoint based on the provided identifier and version.
    
        Args:
            endpoint (str): The SPARQL endpoint URL.
            identifier (str): The identifier for the observations.
            version (str): The version of the observations.
    
        Returns:
            pandas.DataFrame: A DataFrame containing the observations with columns for observation, predicate, and value.
    """
    match endpoint:
        case "TEST":
            endpoint = "https://test.lindas.admin.ch/query"
        case "INT":
            endpoint = "https://int.lindas.admin.ch/query"
        case "PROD":
            endpoint = "https://lindas.admin.ch/query"
    cube_uri = get_cube(endpoint=endpoint, identifier=identifier, version=version)
    query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sh: <http://www.w3.org/ns/shacl#>
        PREFIX schema: <http://schema.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX cube: <https://cube.link/>
        
        SELECT ?obs ?pred ?value
        {{
            <{cube_uri}> cube:observationSet/cube:observation ?obs .
            <{cube_uri}> cube:observationConstraint/sh:property ?dim .
            ?dim sh:path ?predURI ;
               schema:name ?pred .
            FILTER(LANG(?pred)='de')
            {{
               ?dim a cube:KeyDimension .
               ?obs ?predURI ?vl .
               ?vl schema:name ?value
            }} UNION {{
               ?dim a cube:KeyDimension .
               ?obs ?predURI ?value .
               FILTER (DATATYPE(?value) != xsd:anyURI)
            }} UNION {{
               ?dim a cube:MeasureDimension .
               ?obs ?predURI ?value
            }}
        }}
    """

    df = sparql_dataframe.get(endpoint, query)
    observations = df.pivot(index="obs", columns="pred", values="value").reset_index(drop=True)
    return observations
