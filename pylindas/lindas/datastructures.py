from rdflib import Graph
from pylindas.lindas.namespaces import *

class DataStructure:
    def __init__(self, prefix = None, namespace = None):
        self._graph = Graph(bind_namespaces="none")
        for prfx, nmspc in Namespaces.items():
            self._graph.bind(prefix=prfx, namespace=nmspc)
        try:
            self._graph.bind(prefix=prefix, namespace=Namespace(namespace))
        except KeyError:
            print("no Namespace")
            pass

    def serialize(self, filename: str, format='turtle'):
        self._graph.serialize(destination=filename, format=format, encoding="utf-8")

    def add(self, triples):
        self._graph.add(triples)

    def query(self, query: str, kind = "SELECT"):
        match type:
            case "ASK":
                result = self._graph.query(query)
            case "SELECT":
                result = self._graph.query(query).bindings[0]
            case "_":
                result = self._graph.query(query)

        return result
