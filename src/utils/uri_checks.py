# this utility file will contain all the functions that will be used to check the URI

import requests
import re
import json
import time
from utils.singleton.location import Location
from utils.singleton.logger import get_logger

logger = get_logger()

#function to check if the URI is valid
def check_uri(uri):
    '''
    this function will check if the URI is valid
    :param uri: the URI to check
    :return: True if valid, False if not
    '''
    logger.info(f"Checking URI status code :{uri}")
    try:
        response = get_url(uri)
        if response.status_code == 200:
            logger.info(f"URI {uri} is valid")
            return True
        else:
            logger.error(f"URI {uri} is not valid")
            return False
    except Exception as e:
        logger.error(f"URI {uri} is not valid")
        return False

def check_if_json_return(uri):
    '''
    this function will check if the URI returns a json
    :param uri: the URI to check
    :return: True if valid, False if not
    '''
    logger.info(f"Checking URI response type :{uri}")
    try:
        response = get_url(uri)
        if response.status_code == 200:
            if "application/json" in response.headers['Content-Type']:
                logger.info(f"URI {uri} returns a json")
                return True
            else:
                logger.error(f"URI returned {response.headers['Content-Type']} instead of application/json")
                return False
        else:
            logger.error(f"URI {uri} response type is not valid")
            return False
    except Exception as e:
        logger.error(f"URI {uri} response type is not valid")
        return False

def get_url(uri):
    time.sleep(0.3)
    return requests.get(uri)

def check_uri_content(uri):
    '''
    This function will check the content of the uri.
    it will first send out a request with the resonse header set to application/ld+json and check if the response is valid
    if it is not valid it will send out a request with the response header set to application/json and check if the response is valid
    if not send out a normal request and check if the response is valid
    if valid then check in the head of the html of there is a <link href="./ro-crate-metadata.json" rel="describedby" type="application/ld+json"> tag
    the href of this tag will become the new uri
    :param uri: the uri to check
    :return: True/False or the new uri to check
    '''
    logger.info(f"Checking URI content :{uri}")
    try:
        #do the call with requests header set to application/ld+json
        response = requests.get(uri, headers={'Accept': 'application/ld+json'})
        logger.debug(response.headers['content-type'])
        if "application/ld+json" in response.headers['content-type']:
            return True
        #do the call with requests header set to application/json
        if "application/json" in response.headers['content-type']:
            return True
        #do the call with no requests header
        response = requests.get(uri)
        if response.status_code == 200:
            #check if the html contains a <link href="./ro-crate-metadata.json" rel="describedby" type="application/ld+json"> tag
            #./ro-crate-metadata.json can be anything so regex will be used even htts://www.google.com/ro-crate-metadata.json
            regex = r"<link href=\"(.*)\" rel=\"describedby\" type=\"application/ld\+json\">"
            matches = re.finditer(regex, response.text, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                logger.info(f"URI {uri} contains a <link href=\"{match.group(1)}\" rel=\"describedby\" type=\"application/ld+json\"> tag")
                return match.group(1)
            logger.error(f"URI {uri} does not contain a <link href=\"./ro-crate-metadata.json\" rel=\"describedby\" type=\"application/ld+json\"> tag")
            return False
        else:
            logger.error(f"URI {uri} is not valid")
            return False
    except Exception as e:
        logger.error(f"URI {uri} is not valid")
        return False