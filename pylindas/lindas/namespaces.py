from rdflib import Namespace


CUBE = Namespace("https://cube.link/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
LDADMIN = Namespace("https.//ld.admin.ch/application/")
META = Namespace("https://cube.link/meta/")
QUDT = Namespace("http://qudt.org/schema/qudt/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RELATION = Namespace("https://cube.link/relation/")
SCHEMA = Namespace("http://schema.org/")
SH = Namespace("http://www.w3.org/ns/shacl#")
TIME = Namespace("http://www.w3.org/2006/time#")
UNIT = Namespace("http://qudt.org/vocab/unit/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
VOID = Namespace("http://rdfs.org/ns/void#")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
SD_MD = Namespace("https://cube-creator.zazuko.com/shared-dimensions/vocab#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

Namespaces = {
    "cube": CUBE,
    "dcat": DCAT,
    "dct": DCT,
    "schema": SCHEMA,
    "sh": SH,
    "foaf": FOAF,
    "ldadmin": LDADMIN,
    "meta": META,
    "qudt": QUDT,
    "rdf": RDF,
    "relation": RELATION,
    "time": TIME,
    "unit": UNIT,
    "vcard": VCARD,
    "void": VOID,
    "geo": GEO,
    "skos": SKOS,
    "sd_md": SD_MD,
    "xsd": XSD,
}
