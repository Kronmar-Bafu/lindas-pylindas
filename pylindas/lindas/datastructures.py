from rdflib import Graph
from pylindas.lindas.namespaces import *

class DataStructure:
    def __init__(self, prefix = None, namespace = None):
        self.graph = Graph(bind_namespaces="none")
        for prfx, nmspc in Namespaces.items():
            self.graph.bind(prefix=prfx, namespace=nmspc)
        try:
            self.graph.bind(prefix=prefix, namespace=Namespace(namespace))
        except KeyError:
            print("no Namespace")
            pass

    def __str__(self) -> str:
        return f"pylindas.DataStructure with {self.size()} triples."

    # def __add__(self, other):
    #     self.graph += other.graph
    #
    # def __iadd__(self, other):
    #     self.graph += other.graph

    def serialize(self, filename: str, format='turtle'):
        self.graph.serialize(destination=filename, format=format, encoding="utf-8")

    def add(self, triples):
        self.graph.add(triples)

    def remove(self, triples):
        self.graph.remove(triples)

    def query(self, query: str, kind = "SELECT"):
        match kind:
            case "ASK":
                result = self.graph.query(query)
                with open('dummy.txt', 'w') as f:
                    f.write(str(result))
            case "SELECT":
                result = self.graph.query(query)
            case "_":
                result = self.graph.query(query)

        return result

    def size(self):
        how_many_triples_query = (
            "SELECT (COUNT(*) as ?Triples)"
            "WHERE {"
            "    ?s ?p ?o."
            "}"
        )
        how_many_triples = self.graph.query(how_many_triples_query, kind="SELECT").get("Triples").value
        return how_many_triples

