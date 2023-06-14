#this utility file will help with getting metadata from a given uri

import requests
import json
import rdflib
import os
import sys
import time
import re
#from utils.singleton.logger import get_logger

#logger = get_logger()

#class here that will handle all actions related to a given uri
class Metadata():
    def __init__(self, uri):
        self.uri = uri
        self.og_uri = uri
        self.metadata = {}
        self.type_of_metadata : str = None
        self.kg = rdflib.Graph()
        self.uri_change = True
        self.error = False
        
        while self.uri_change:
            self.get_metadata()
            
    
    def get_metadata(self):
        '''
        try and get the metadata from the uri provided.
        First do request to the uri with content negotiation to get the metadata.
        The types to negotiate are: application/json, application/rdf+xml, application/rdf+json, application/ld+json, text/turtle
        If the request is successful then then set self.metadata "mimetype" to the mimetype of the response and set self.metadata "data" to the response data
        if request is not successful then look into the head of the uri and see if there is a property link with rel=describedby that has link to the metadata
        if there is a link then try and get the metadata from the link and then set self.uri to the link and self.uri_change to True
        if there is no link then set self.uri to self.uri+ro-crate-metadata.json and self.uri_change to True
        '''
        self.uri_change = False
        mime_types = ["application/json", "application/rdf+xml", "application/rdf+json", "application/ld+json", "text/turtle"]
        for mime_type in mime_types:
            try:
                response = requests.get(self.uri, headers={"Accept": mime_type})
                time.sleep(0.3)
                print("trying to get metadata from uri {0} with mimetype {1}".format(self.uri, mime_type))
                if response.status_code == 200:
                    print("content type: {0}".format(response.headers["Content-Type"]))
                    #check if the response data mimetype is one of the mime_types
                    #if it is then set self.metadata "mimetype" to the mimetype of the response and set self.metadata "data" to the response data
                    #if it is not then set self.uri to self.uri+ro-crate-metadata.json and self.uri_change to True
                    if mime_type in response.headers["Content-Type"]:
                        self.metadata["mimetype"] = mime_type
                        self.metadata["data"] = response.text
                        break
            except Exception as e:
                #logger.error(msg="Error getting metadata from uri {0} with mimetype {1} : {2}".format(self.uri, mime_type, str(e)))
                self.error = True
                pass
            
        if "mimetype" not in self.metadata:
            try:
                response = requests.get(self.uri)
                #print(response.text)
                if response.status_code == 200:
                    #perform search with regex to find the link with rel=describedby in the html head section of the uri
                    #if there is a link then get then set href to self.uri and self.uri_change to True and also check if the type is one of the mime_types
                    #if there is no link then set self.uri to self.uri+ro-crate-metadata.json and self.uri_change to True
                    #split the response text into lines and then search each line for the link with rel=describedby
                    for line in response.text.split("<link"):
                        lin_elemets = line.split("/>")
                        for element in lin_elemets:
                            if "rel=describedby" in element:
                                print(element)
                                #get the href from the element and then check if the href is a full uri or a relative uri
                                self.uri_change = True
                                if self.uri[-1] == "/":
                                    self.uri = self.uri + element.split("href=")[1].split(" ")[0].replace('"', '')[2:]
                                else:
                                    self.uri = self.uri + element.split("href=")[1].split(" ")[0].replace('"', '')[1:]
                                #check if type is in element
                                if "type=" in element:
                                    type = element.split("type=")[1].split(" ")[0].replace('"', '')
                                    if type in mime_types:
                                        self.metadata["mimetype"] = type
                                        break
                    
                    if not self.uri_change:
                        #if uri ends with ro-crate-metadata.json then set self.uri_change to False
                        if self.uri.endswith("ro-crate-metadata.json"):
                            self.uri_change = False
                        else:
                            if self.uri[-1] == "/":
                                self.uri = self.uri + "ro-crate-metadata.json"
                            else:
                                self.uri = self.uri + "/ro-crate-metadata.json"
                            self.uri_change = True
            except Exception as e:
                #logger.error(msg="Error getting metadata from uri {0} : {1}".format(self.uri, str(e)))
                self.error = True
                pass
    
    def is_error(self):
        return self.error
                
test = Metadata("https://data.arms-mbon.org/")
print(test.metadata)
print(test.uri)
print(test.uri_change)

test2 = Metadata("https://cedricdcc.github.io/test_single_rocrate/latest/")
print(test2.metadata)
print(test2.uri)
print(test2.uri_change)