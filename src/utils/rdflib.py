#this file will contain all the helper functions for adding and abstracting data to the registry knowledge base
import rdflib
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF, RDF, RDFS, XSD
import os
import sys
import json 
import requests
#logger
from utils.singleton.logger import get_logger
from utils.singleton.location import Location

logger = get_logger()
class KnowledgeGraphRegistry():
    
    def __init__(self, knowledgeGraph):
        logger.info(msg="Initializing Knowledge Graph Registry")
        if knowledgeGraph is None:
            self.knowledgeGraph = Graph()
            #add triple that states that the current uri ./ is a schema:CreativeWork
            self.knowledgeGraph.add((URIRef("./"), RDF.type, URIRef("http://schema.org/CreativeWork")))
            #add triple that is a blank node named "listregistry" that is part of the registry hasPart
            self.knowledgeGraph.add((URIRef("./"), URIRef("http://schema.org/hasPart"), BNode("listregistry")))    
            #define listregistry as a schema:ItemList
            self.knowledgeGraph.add((BNode("listregistry"), RDF.type, URIRef("http://schema.org/ItemList")))
            #define the name of the listregistry as "registry of all profiles "
            self.knowledgeGraph.add((BNode("listregistry"), URIRef("http://schema.org/name"), Literal("registry of all profiles")))
            #define that listregistry is schema part of the current uri
            self.knowledgeGraph.add((BNode("listregistry"), URIRef("http://schema.org/isPartOf"), URIRef("./")))
        else:
            self.knowledgeGraph = knowledgeGraph
            
    def addJson(self, json):
        self.knowledgeGraph.parse(data=json, format="json-ld")
    
    def toTurtle(self):
        return self.knowledgeGraph.serialize(format="turtle")
    
    def toJson(self):
        return self.knowledgeGraph.serialize(format="json-ld")
    
    def toRdf(self):
        return self.knowledgeGraph.serialize(format="xml")
    
    def addProfile(self, profile_uri, profile_data):
        logger.info(msg="Adding profile to the registry {0}".format(profile_uri))
        #add the profile_uri to the blank node listregistry as a listItem
        self.knowledgeGraph.add((BNode("listregistry"), URIRef("http://schema.org/itemListElement"), URIRef(profile_uri)))
        #add the jsonld data to the knowledge graph
        try:
            #first add the uri as rdf type schema:CreativeWork , schema:LisItem
            self.knowledgeGraph.add((URIRef(profile_uri), RDF.type, URIRef("http://schema.org/CreativeWork")))
            self.knowledgeGraph.add((URIRef(profile_uri), RDF.type, URIRef("http://schema.org/ListItem")))
            self.knowledgeGraph.add((URIRef(profile_uri), URIRef("http://schema.org/item"), URIRef(profile_uri)))
            self.knowledgeGraph.parse(data=profile_data, format="json-ld")   
        except Exception as e:
            logger.error(msg="Error parsing profile data: " + str(e))
            logger.exception(e)
            return False