# this utility file will contain all the functions that will be used to check the URI

import os
import sys
import requests
import yaml
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