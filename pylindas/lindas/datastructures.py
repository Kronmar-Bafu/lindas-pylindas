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

    def __str__(self) -> str:
        return f"pylindas.DataStructure with {self.size()} triples."

    def __add__(self, other):
        return self._graph + other._graph

    def __iadd__(self, other):
        return self._graph + other._graph

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

    def size(self):
        how_many_triples_query = (
            "SELECT (COUNT(*) as ?Triples)"
            "WHERE {"
            "    ?s ?p ?o."
            "}"
        )
        how_many_triples = self._graph.query(how_many_triples_query, kind="SELECT").get("Triples").value
        return how_many_triples

