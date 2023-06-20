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
    
    def __init__(self, base, knowledgeGraph=None):
        logger.info(msg="Initializing Knowledge Graph Registry")
        self._base = base
        if knowledgeGraph is not None:
            self.knowledgeGraph = knowledgeGraph
            return 
        # else
        self.knowledgeGraph = Graph()
        #bind the schema namespace to the prefix schema
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
            
            
    def write(self, file_name, format="turtle"):
        logger.info(msg="Writing Knowledge Graph Registry to file {0}".format(file_name))
        self.knowledgeGraph.bind("schema", "http://schema.org/", override=True, replace=True)
        destinaton = os.path.join(Location().get_location(), "build",file_name)
        self.knowledgeGraph.serialize(destination=destinaton, format=format, base=self._base)
            
    def addJson(self, json):
        self.knowledgeGraph.parse(data=json, format="json-ld")
    
    def toTurtle(self):
        return self.write(file_name="registry.ttl", format="turtle")
    
    def toJson(self):
        return self.write(file_name="registry.json", format="json-ld")
    
    def toRdf(self):
        return self.write(file_name="registry.rdf", format="xml")
    
    def addProfile(self, profile_uri):
        logger.info(msg="Adding profile to the registry {0}".format(profile_uri))
        #add the profile_uri to the blank node listregistry as a listItem
        self.knowledgeGraph.add((BNode("listregistry"), URIRef("http://schema.org/itemListElement"), URIRef(profile_uri)))
        #add the jsonld data to the knowledge graph
        try:
            #first add the uri as rdf type schema:CreativeWork , schema:LisItem
            #self.knowledgeGraph.add((URIRef(profile_uri), RDF.type, URIRef("http://schema.org/CreativeWork")))
            self.knowledgeGraph.parse(format="json-ld", location=URIRef(profile_uri))
            self.knowledgeGraph.add((URIRef(profile_uri), RDF.type, URIRef("http://schema.org/ListItem")))
            self.knowledgeGraph.add((URIRef(profile_uri), URIRef("http://schema.org/item"), URIRef(profile_uri)))
            
        except Exception as e:
            logger.error(msg="Error parsing profile data: " + str(e))
            logger.exception(e)
            return False
        
        #function to extract metadata information from all the profiles in the registry
        #this function will return a dictionary with the following structure
        #{
        #   "profile_uri": {
        #       "name": "profile name",
        #       "description": "profile description",
        #       "author": "profile author",
        #       "dateCreated": "profile date created",
        #       "dateModified": "profile date modified",
        #       "version": "profile version",
        #       "license": "profile license",
        #       "keywords": "profile keywords",
        #       "url": "profile url"
        #   }
        #}
    def extractMetadata(self):
        '''
        this function will extract metadata from all the profiles in the registry
        '''
        logger.info(msg="Extracting metadata from all profiles in the registry")
        #create a dictionary to store the metadata
        metadata = {}
        #get all the profiles in the registry
        profiles = self.knowledgeGraph.objects(BNode("listregistry"), URIRef("http://schema.org/itemListElement"))
        #iterate over all the profiles
        for profile in profiles:
            #get the metadata from the profile
            metadata[profile] = self.getMetadata(profile)
        #log json metadata in pprint format
        logger.debug(msg="Metadata extracted from all profiles in the registry: \n{0}".format(json.dumps(metadata, indent=4)))
        return metadata
    
    def getMetadata(self, profile_uri):
        '''
        this function will extract metadata from a profile
        '''
        logger.info(msg="Extracting metadata from profile {0}".format(profile_uri))
        #create a dictionary to store the metadata
        metadata = {}
        #get the name of the profile
        metadata["name"] = self.knowledgeGraph.value(profile_uri, URIRef("http://schema.org/name"))
        #get the description of the profile
        metadata["description"] = self.knowledgeGraph.value(profile_uri, URIRef("http://schema.org/description"))
        #get the authors of the profile, this can be a list of authors or a single author
        all_authors = self.knowledgeGraph.query("""SELECT ?authors WHERE {
            <%s> <http://schema.org/author> ?authors .
        }""" % profile_uri)
        #if there is more than one author
        if len(all_authors) > 1:
            #create a list to store the authors
            authorse = []
            #iterate over all the authors
            for row in all_authors:
                #add the author to the list
                authorse.append(row.authors)
            #add the list of authors to the metadata
            metadata["author"] = authorse
        else:
            metadata["author"] = self.knowledgeGraph.value(profile_uri, URIRef("http://schema.org/author"))
        #get the dateCreated of the profile
        metadata["dateCreated"] = self.knowledgeGraph.value(profile_uri, URIRef("http://schema.org/dateCreated"))
        #get the dateModified of the profile
        metadata["dateModified"] = self.knowledgeGraph.value(profile_uri, URIRef("http://schema.org/dateModified"))
        #get the version of the profile
        metadata["version"] = self.knowledgeGraph.value(profile_uri, URIRef("http://schema.org/version"))
        #get the license of the profile
        metadata["license"] = self.knowledgeGraph.value(profile_uri, URIRef("http://schema.org/license"))
        #get the keywords of the profile this can be a list of keywords or a single keyword
        #perform sparql query to get all the keywords
        all_keywords = self.knowledgeGraph.query("""SELECT ?keywords WHERE {
            <%s> <http://schema.org/keywords> ?keywords .
        }""" % profile_uri)
        metadata["keywords"] = []
        if len(all_keywords) > 1:
            #iterate over all the keywords
            for keyworde in all_keywords:
                metadata["keywords"].append(keyworde.keywords)
            #get the url of the profile
            metadata["url"] = profile_uri
        else:
            metadata["keywords"] = self.knowledgeGraph.value(profile_uri, URIRef("http://schema.org/keywords"))
        #log json metadata in pprint format
        logger.debug(msg="Metadata extracted from profile {0}: \n{1}".format(profile_uri, json.dumps(metadata, indent=4)))
        return metadata
    
    
    