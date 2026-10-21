from pyshacl import validate as pyshacl_validate
from rdflib import Graph

def validate(data_graph: Graph, shacl_graph: Graph) -> tuple:
    conforms, results_graph, text = pyshacl_validate(data_graph, shacl_graph=shacl_graph, abort_on_first=True, inference="none", advanced=True)
    return conforms, text
