#this file will contain all functions that will be important to get info from a json file 
import csv
import json
from utils.singleton.location import Location
from utils.singleton.logger import get_logger

logger = get_logger()

def has_conformsTo_prop(json_data):
    try:
        for entry in json_data["@graph"]:
            #check if entry contains conformsTo, if it does check if it is an array and if it is check if it contains Profile or Dataset
            if "conformsTo" in entry:
                return True 
    except Exception as e:
        logger.error(f"Error while getting conformsTo of json file: {e}")
        return None
    
def get_cornformTo_uris(json_data):
    try:
        uris = []
        for entry in json_data["@graph"]:
            #check if entry contains conformsTo, if it does check if it is an array and if it is check if it contains Profile or Dataset
            if "conformsTo" in entry:
                if type(entry["conformsTo"]) == list:
                    for conformity in entry["conformsTo"]:
                        uris.append(conformity)
                else:
                    uris.append(entry["conformsTo"])
        if len(uris) == 0:
            logger.warning("No conformsTo found")
            return None
        return uris
    except Exception as e:
        logger.error(f"Error while getting conformsTo prop of json file: {e}")
        return None
    
def is_profile(json_data):
    try:
        for entry in json_data["@graph"]:
            if type(entry["@type"]) == list:
                for typen in entry["@type"]:
                    if typen == "Profile":
                        return True
            else:
                if entry["@type"] == "Profile":
                    return True 
    except Exception as e:
        logger.error(f"Error while getting type of json file: {e}")
        return None
    
def get_profile_prop(json_data):
    try:
        for entry in json_data["@graph"]:
            if type(entry["@type"]) == list:
                for typen in entry["@type"]:
                    if typen == "Profile":
                        return entry["@id"]
            else:
                if entry["@type"] == "Profile":
                    return entry["@id"]
        logger.warning("No profile found")
        return None
    except Exception as e:
        logger.error(f"Error while getting type of json file: {e}")
        return None
    
def get_metadata_profile(json_data):
    '''
    This function will return the metadata of a json file. 
    This includes: 
        - "author": list of strings or string 
        - "description": string
        - "keywords": list of strings or string
        - "license": dict with @id key with value string
        - "name": string
        - "version": string 
    These properties should be located in the @id: ./
    The return is a dict with the above keys and values. If a key is not found, the value will be None
    :param json_data: json data
    :return: dict with metadata
    '''
    try:
        for entry in json_data["@graph"]:
            if entry["@id"] == "./":
                metadata = {}
                if "author" in entry:
                    metadata["author"] = entry["author"]
                else:
                    metadata["author"] = None
                if "description" in entry:
                    metadata["description"] = entry["description"]
                else:
                    metadata["description"] = None
                if "keywords" in entry:
                    metadata["keywords"] = entry["keywords"]
                else:
                    metadata["keywords"] = None
                if "license" in entry:
                    metadata["license"] = entry["license"]["@id"]
                else:
                    metadata["license"] = None
                if "name" in entry:
                    metadata["name"] = entry["name"]
                else:
                    metadata["name"] = None
                if "version" in entry:
                    metadata["version"] = entry["version"]
                else:
                    metadata["version"] = None
                return metadata
    except Exception as e:
        logger.error(f"Error while getting metadata of json file: {e}")
        logger.exception(e)
        return None