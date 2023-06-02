#this file will contain all the functions that will be used to build the registry that will be used to build the gh-pages
import os
import sys
import yaml
import csv
import json
from utils.singleton.location import Location
from utils.singleton.logger import get_logger
from utils.uri_checks import check_uri, check_if_json_return, get_url, check_uri_content
logger = get_logger()

#registry class that will hold the registry
class Registry():
    def __init__(self, registry=None):
        self.registry = registry
        self.error_rows = []
        self.warnings_rows = []
        self.profile_rows = []
        self.profile_registry_array = []
    
    def __repr__(self) -> str:
        return f"Registry(registry={self.registry})"
    
    def get_report(self):
        logger.info("Generating report")
        report = {}
        report["error_rows"] = self.error_rows
        report["warnings_rows"] = self.warnings_rows
        report["profile_rows"] = self.profile_rows
        report["profile_registry_array"] = self.profile_registry_array
        logger.info(
            json.dumps(
                report,
                indent=4
            )
        )
        return report
    
    def get_registry(self):
        return self.registry
    
    def build_registry(self, data_path):
        '''
        this function will build the registry
        :param data_path: the path to the data folder
        :return: the registry
        '''
        logger.info("Building registry")
        #function here to detect all the csv files in the data_path including subfolders
        self.csv_files = self.detect_csv_files(data_path)
        logger.info(f"Found {len(self.csv_files)} csv files")
        #function that will go over all the csv files and return an array of dictionaries with each entry in the array being {"source": "relative path to csv file", "URI": "URI of a given profile", "contact":"contact" }
        self.registry_array = self.make_registry_array()
        self.registry_array_check()

    def detect_csv_files(self, data_path):
        '''
        this function will detect all the csv files in the data_path including subfolders
        :param data_path: the path to the data folder
        :return: the list of csv files
        '''
        logger.info("Detecting csv files")
        csv_files = []
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith(".csv"):
                    csv_files.append(os.path.join(root, file))
        return csv_files
    
    def make_registry_array(self):
        '''
        this function will go over all the csv files and return an array of dictionaries with each entry in the array being {"source": "relative path to csv file", "URI": "URI of a given profile", "contact":"contact" }
        :param csv_files: the list of csv files
        :return: the array of dictionaries
        '''
        logger.info("Making registry array")
        registry_array = []
        try:
            for csv_file in self.csv_files:
                logger.info(f"Reading csv file {csv_file}")
                with open(csv_file, newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        registry_array.append({"source": csv_file, "URI": row["URI"], "contact": row["contact"]})
        except Exception as e:
            logger.error(f"Error while making registry array: {e}")

        return registry_array
    
    def registry_array_check(self):
        '''
        this function will make the registry
        :param registry_array: the array of dictionaries
        :return: the registry
        '''
        logger.info("Making registry")
        
        for entry in self.registry_array:
            logger.info(f"Checking entry {entry}")
            #check if the URI is valid
            #check if the URI is already in the registry
            warning = False
            for row  in self.profile_rows:
                if entry["URI"] == row["URI"]:
                    logger.warning(f"URI {entry['URI']} already in registry")
                    self.warnings_rows.append(entry)
                    warning = True
                    break
            
            if warning:
                continue
                
            if not check_uri(entry["URI"]):
                self.error_rows.append(entry)
                continue
            
            var_check_uri_content = check_uri_content(entry["URI"])
            # check if check_uri_content is True or False
            if var_check_uri_content != False and var_check_uri_content != True:

                #check if var_check_uri_content starts with http
                if var_check_uri_content.startswith("http"):
                    entry["URI"] = var_check_uri_content
                else: 
                    if var_check_uri_content.startswith("./"):
                        entry["URI"] = entry["URI"] + var_check_uri_content[1:]
                    else:
                        logger.error(f"URI {entry['URI']} is not valid")
                        self.error_rows.append(entry)
                self.profile_rows.append(entry)
                continue
            
            if not var_check_uri_content:
                self.error_rows.append(entry)
                continue
            
            #check if the URI return a valid json-ld
            self.profile_rows.append(entry)
    
    def get_type_json_file(self,uri):
        '''
        this function will get the json file from a uri and look into the jsonfile
        @graph [] for @id ./ and check if the @type is an array and if it is check if it contain Profile or Dataset
        :param uri: the uri to the json file    
        :return: the type of the json file
        '''
        logger.info("Getting type of json file")
        #get the json file
        json_data = get_url(uri)
        #check if the json file is valid
        pass
         