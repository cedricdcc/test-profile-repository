#this file will contain the profileharvester class

import requests
import re
import json
import rdflib
import time
from utils.singleton.location import Location
from utils.singleton.logger import get_logger

logger = get_logger()

class ProfileHarvester():
    def __init__(self, uri):
        self.entry_uri = uri  #rename entry_uri
        # add state var for set of profiles (ie _uri) harvested from entry_uri
        self.entry_uri_content = None  #rename entry_content
        self.entry_uri_content_type = None #this will be categorically set to ["profile","crate","registry","other"]
        self.entry_uri_type = None
        self.bad_entry_uri = False
        self.check_again = True
        self.profiles = set() #set of profiles harvested from entry_uri
        self.kg = rdflib.Graph()
        self.children = []
         
    def harvest(self):
        '''
        this function will harvest the metadata from the uri provided
        '''
        while self.check_again:
            self.check_entry_uri_content_and_type()
        
        if self.entry_uri_type == None:
            self.bad_entry_uri = True
        
        self.insert_metadata()
        self.extract_type_from_kg()        
        logger.info(msg="Finished harvesting metadata from uri {0}".format(self.entry_uri))
        logger.info(msg="harvested profiles: {0}".format(self.profiles))

    def check_entry_uri_content_and_type(self):
        '''
        try and get the metadata from the uri provided.
        First do request to the uri with content negotiation to get the metadata.
        The types to negotiate are: application/json, application/rdf+xml, application/rdf+json, application/ld+json, text/turtle
        If the request is successful then then set self.metadata "mimetype" to the mimetype of the response and set self.metadata "data" to the response data
        if request is not successful then look into the head of the uri and see if there is a property link with rel=describedby that has link to the metadata
        if there is a link then try and get the metadata from the link and then set self.uri to the link and self.uri_change to True
        if there is no link then set self.uri to self.uri+ro-crate-metadata.json and self.uri_change to True
        '''
        self.check_again = False
        mime_types = ["text/turtle", "application/ld+json", "application/rdf+xml", "application/json"]
        for mime_type in mime_types:
            try:
                response = requests.get(self.entry_uri, headers={"Accept": mime_type})
                time.sleep(0.3) #check if lib exists to do this ratelimit
                logger.debug("trying to get metadata from entry_uri {0} with mimetype {1}".format(self.entry_uri, mime_type))
                if response.status_code == 200:
                    logger.debug("content type: {0}".format(response.headers["Content-Type"]))
                    #check if the response data mimetype is one of the mime_types
                    #if it is then set self.metadata "mimetype" to the mimetype of the response and set self.metadata "data" to the response data
                    #if it is not then set self.uri to self.uri+ro-crate-metadata.json and self.uri_change to True
                    if mime_type in response.headers["Content-Type"]:
                        self.entry_uri_type= mime_type
                        self.entry_uri_content = response.text
                        break
            except Exception as e:
                logger.error(msg="Error getting metadata from entry_uri {0} with mimetype {1} : {2}".format(self.entry_uri, mime_type, str(e)))
                self.bad_entry_uri = True
                break
        
        if self.entry_uri_type == None:
            logger.debug("trying to get metadata from entry_uri {0} with mimetype {1}".format(self.entry_uri, "text/html"))
            #first look into header of the uri
            headers = response.headers
            logger.debug("headers: {0}".format(headers))
            if "Link" in headers:
                for link in headers["Link"].split(","):
                    if "rel=describedby" in link:
                        self.check_again = True
                        uri_link = link.split(" ")[0].replace("<", "").replace(">", "")
                        
                        if uri_link.startswith("./"):
                            self.entry_uri = self.entry_uri + uri_link[1:]
                        else:
                            self.entry_uri = uri_link
                        logger.debug("entry_uri changed to {0}".format(self.entry_uri))
                        #check if type is in link
                        if "type=" in link:
                            typee = link.split("type=")[1].split(" ")[0].replace('"', '')
                            if typee in mime_types:
                                self.entry_uri_type = typee
                                break
            
            try:
                response = requests.get(self.entry_uri)
                if response.status_code == 200 and "text/html" in response.headers["Content-Type"]:
                    logger.debug("checking html for link with rel=describedby")
                    #rewrite using beautiful soup
                    for line in response.text.split("<link"):
                        lin_elemets = line.split("/>")
                        for element in lin_elemets:
                            if "rel=describedby" in element:
                                self.check_again = True
                                if self.entry_uri[-1] == "/":
                                    self.entry_uri = self.entry_uri + element.split("href=")[1].split(" ")[0].replace('"', '')[2:]
                                else:
                                    self.entry_uri = self.entry_uri + element.split("href=")[1].split(" ")[0].replace('"', '')[1:]
                                #check if type is in element
                                if "type=" in element:
                                    type = element.split("type=")[1].split(" ")[0].replace('"', '')
                                    if type in mime_types:
                                        self.entry_uri_type = type
                                        break
                    
                    if not self.check_again:
                        if self.entry_uri.endswith("ro-crate-metadata.json"):
                            self.check_again = False
                        else:
                            self.entry_uri = self.entry_uri + "/ro-crate-metadata.json"
                            self.check_again= True
            except Exception as e:
                logger.error(msg="Error getting metadata from entry_uri {0} : {1}".format(self.entry_uri, str(e)))
                self.bad_entry_uri = True
                pass
    
    def is_bad_entry_uri(self):
        return self.bad_entry_uri
    
    def insert_metadata(self):
        '''
        insert the metadata into the graph
        '''
        if self.entry_uri_type == "application/json" or self.entry_uri_type == "application/ld+json":
            self.kg.parse(data=self.entry_uri_content, format="json-ld", base=self.entry_uri)
        elif self.entry_uri_type == "application/rdf+xml":
            self.kg.parse(data=self.entry_uri_content, format="xml", base=self.entry_uri)
        elif self.entry_uri_type == "application/rdf+json":
            self.kg.parse(data=self.entry_uri_content, format="json-ld", base=self.entry_uri)
        elif self.entry_uri_type == "text/turtle":
            #decode the self.entry_uri_content to utf-8
            #entry_uri = self.entry_uri.decode("utf-8")
            self.kg.parse(self.entry_uri, format="turtle") #got an error here when using the base parameter
    
    def get_kg(self):
        #serialize the graph to ttl and return it
        self.getCompleteKG()
        return self.kg.serialize(format="turtle")
    
    def extract_type_from_kg(self):
        '''
        extract the type of kg we are dealing with.
        This can be either a rocrate, profile or registry.
        We do this by looking for specific triples in the graph.
        '''    
        #run number of sparql queries to get sets of discovered profiles
        # 1/ ?prof rdf:type prof:Profile . 
        # 2/ [] schema:conformsTo ?prof . (revisit depth -1)
        # 3/ [] schema:hasPart ?child_uri . (revisit depth -1)
        # 4/ [] schema:itemListElement ?child_uri . (revisit depth -1)
        
        #first check with the following query
        '''
        prefix prof: <http://www.w3.org/ns/dx/prof/>
        select ?profile where { ?profile a prof:Profile . }
        '''
        #if this query returns a result then we have a profile
        #if not then we we perform the following query
        '''
        prefix schema: <http://schema.org/>
        select ?candidate where {
            {?rocrate schema:conformsTo ?candidate .
            [] schema:about ?rocrate .}
            UNION
            {[] schema:hasPart/schema:itemListElement ?candidate .}
            # UNION
            # [] schema:hasPart ?candidate .
        }
        '''
        query = '''
        prefix prof: <http://www.w3.org/ns/dx/prof/>
        select ?profile where { ?profile a prof:Profile . }
        '''
        #before doing the queries change the kg to have the entry_uri as base_uri instead of the file uri
        self.kg
        
        results = self.kg.query(query)
        if len(results) > 0:
            self.type = "profile"
            logger.debug("uri has profile(s)")
            #get the profiles and add them to the set
            for result in results:
                logger.debug("profile: {0}".format(result[0]))
                self.profiles.add(result[0])
            return
        
        query = '''
        prefix schema: <http://schema.org/>
        select ?candidate where {
            {?rocrate schema:conformsTo ?candidate .
            [] schema:about ?rocrate .}
            UNION
            {[] schema:hasPart/schema:itemListElement ?candidate .}
        }
        '''
        results = self.kg.query(query)
        if len(results) > 0:
            #the results are uri that also need to be checked for profiles so we spawn a child thread for each
            for result in results:
                child_uri = result[0]
                logger.debug("child_uri: {0}".format(child_uri))
                child_profile_harvester = ProfileHarvester(child_uri)
                self.children.append(child_profile_harvester)
                child_profile_harvester.harvest()
                
    def getProfiles(self):
        # build profiles , possibly by delegates
        #check if we have children
        if len(self.children) > 0:
            for child in self.children:
                self.profiles = self.profiles.union(child.getProfiles())
        return self.profiles 
    
    def getCompleteKG(self):
        # build profiles , possibly by delegates
        #check if we have children
        if len(self.children) > 0:
            for child in self.children:
                try:
                    self.kg = self.kg + child.getCompleteKG()
                except Exception as e:
                    logger.error(msg="Error getting complete KG from child {0} : {1}".format(child, str(e)))
        return self.kg
    
    def getListDictsProfiles(self):
        #first get the complete kg
        c_kg = self.getCompleteKG()
        #run query that will extract the triples that we need , check for each of the triples if they exist if not return empty string
        query = '''
        prefix prof: <http://www.w3.org/ns/dx/prof/>
        prefix schema: <http://schema.org/>
        select ?profile ?name ?description ?version ?keywords ?license where {
            ?profile a prof:Profile .
            OPTIONAL { ?profile schema:name ?name . }
            OPTIONAL { ?profile schema:description ?description . }
            OPTIONAL { ?profile schema:version ?version . }
            OPTIONAL { ?profile schema:keywords ?keywords . }
            OPTIONAL { ?profile schema:license ?license . }
        }    
        '''
        results = c_kg.query(query)
        toreturn = {}
        for result in results:
            p_dict = {}
            uri = result[0]
            p_dict["name"] = result[1]
            p_dict["description"] = result[2]
            p_dict["version"] = result[3]
            p_dict["keywords"] = result[4]
            p_dict["license"] = result[5]
            toreturn[uri] = p_dict
        return toreturn