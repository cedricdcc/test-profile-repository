#this file will contain all the functions that will be used to build the registry that will be used to build the gh-pages
import os
import csv
import json
from utils.singleton.location import Location
from utils.singleton.logger import get_logger, get_warnings_log
from utils.uri_checks import check_uri, check_if_json_return, get_url, check_uri_content
from utils.jsonld_file import has_conformsTo_prop, get_cornformTo_uris, is_profile, get_profile_prop, get_metadata_profile
from utils.html_build_util import make_html_file, setup_build_folder
from utils.rdflib import KnowledgeGraphRegistry
from utils.contact import Contact
logger = get_logger()

#registry class that will hold the registry
class Registry():
    def __init__(self, registry=None):
        self.registry = registry
        self.error_rows = []
        self.warnings_rows = []
        self.to_check_rows = []
        self.checked_rows = []
        self.profile_registry_array = []
        self.knowledge_graph_registry = KnowledgeGraphRegistry(knowledgeGraph=None)
    
    def __repr__(self) -> str:
        return f"Registry(registry={self.registry})"
    
    def get_report(self):
        logger.info("Generating report")
        report = {}
        report["error_rows"] = self.error_rows
        report["warnings_rows"] = self.warnings_rows
        report["to_check_rows"] = self.to_check_rows
        report["checked_rows"] = self.checked_rows
        report["profile_registry_array"] = self.profile_registry_array
        logger.info(
            json.dumps(
                report,
                indent=4
            )
        )
        
        #get warning logs and write them to the build folder as warnings.txt
        logger.info("Writing warnings to build folder")
        warnings_log = get_warnings_log()
        with open(os.path.join(Location().get_location(), "build", "warnings.txt"), "w") as f:
            for warning in warnings_log:
                f.write(warning)
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
        self.get_type_to_check_rows()
        self.get_conformsTo_uris()
        self.get_metadata_profiles()
        setup_build_folder()
        self.kgttl = self.knowledge_graph_registry.toTurtle()
        logger.debug(self.kgttl)
        #write the knowledge graph to a ttl file
        with open(os.path.join(Location().get_location(), "build", "registry.ttl"), "w") as f:
            f.write(self.kgttl)
        self.registry_json_format = self.knowledge_graph_registry.extractMetadata()
        self.make_html_file_registry()

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
                        registry_array.append({"source": csv_file, "URI": row["URI"], "contact": Contact(row["contact"])})
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
            #first check if the contact is valid
            logger.debug(f"Checking contact {entry['contact'].get_contact()}")
            if not entry["contact"].result():
                logger.warning(f"Contact {entry['contact'].get_contact()} is not valid")
                self.warning_row(entry, reason="Contact is not valid")
                continue
            
            logger.info(f"Checking entry {entry}")
            #check if the URI is valid
            #check if the URI is already in the registry
            warning = False
            for row  in self.to_check_rows:
                if entry["URI"] == row["URI"]:
                    logger.warning(f"URI {entry['URI']} already in registry")
                    self.warning_row(entry, reason="URI already in registry")
                    warning = True
                    break
            
            if warning:
                continue
                
            if not check_uri(entry["URI"]):
                self.failed_row(entry, reason="URI is not valid")
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
                        logger.warning(f"URI {entry['URI']} is not valid")
                        self.failed_row(entry, reason="URI is not valid")
                self.to_check_rows.append(entry)
                continue
            
            if not var_check_uri_content:
                self.failed_row(entry, reason="URI is not valid")
                continue
            
            #check if the URI return a valid json-ld
            self.to_check_rows.append(entry)

    def get_type_to_check_rows(self):
        logger.debug(f"{len(self.to_check_rows)} rows to check")
        for row in self.to_check_rows:
            logger.info(f"Getting type of {row}")
            row["type"] = self.get_type_json_file(row["URI"])
            if row["type"] == "profile":
                row["profile_prop"] = get_profile_prop(get_url(row["URI"]).json())
                self.approved_row(row)
            elif row["type"] == "crate":
                row["conformsTo_uris"] = get_cornformTo_uris(get_url(row["URI"]).json())
            else:
                self.failed_row(row, reason="Type is not profile or crate")
        
        self.remove_checked_rows()
    
    def get_uri_from_prop(self, prop):
        '''
        this function will get a uri from a prop
        :param prop: the prop to get the uri from
        :return: the uri
        '''
        logger.info("Getting id from prop")
        try:
            #check if given prop is object
            if type(prop) == dict:
                #check if the prop contains an @id
                if "@id" in prop:

                    #check if the @id is a valid uri or starts with ./
                    if check_uri(prop["@id"]) or prop["@id"].startswith("./"):
                        return prop["@id"]
                else:
                    logger.warning("No id found in prop")
                    return None
            else:
                logger.warning("Prop is not an object")
                return None
        except Exception as e:
            logger.error(f"Error while getting id from prop: {e}")
            return None

    def get_conformsTo_uris(self):
        for row in self.to_check_rows:
            try:
                if row["type"] == "crate":
                    #check if the conformsTo prop is an array
                    if type(row["conformsTo_uris"]) == list:
                        profile_found = False
                        for conformrow in row["conformsTo_uris"]:
                            uri_from_prop = self.get_uri_from_prop(conformrow)
                            logger.debug(f"URI from prop: {uri_from_prop}")
                            #check if the conformsTo prop contains a profile
                            if check_uri(uri_from_prop):
                                try:
                                    if is_profile(get_url(uri_from_prop).json()):
                                        #check if row already has a profile prop, if it does then append the new profile prop to the existing one
                                        if "profile_prop" in row:
                                            row["profile_prop"] = row["profile_prop"] + "," + get_profile_prop(get_url(uri_from_prop).json())
                                        else:
                                            row["profile_prop"] = get_profile_prop(get_url(uri_from_prop).json())
                                        profile_found = True
                                except Exception as e:
                                    logger.debug(f"URI check for {uri_from_prop} failed")
                                    logger.error(f"Error while getting conformsTo uris: {e}")
                                    continue
                        if profile_found:
                            self.approved_row(row)
                        else:
                            self.warning_row(row, reason="No profile found in conformsTo prop")
                    else:
                        #check if the conformsTo prop contains a profile
                        uri_from_prop = self.get_uri_from_prop(row["conformsTo_uris"])
                        logger.debug(f"URI from prop: {uri_from_prop}")
                        if check_uri(uri_from_prop):
                            if is_profile(get_url(uri_from_prop).json()):
                                row["profile_prop"] = get_profile_prop(get_url(uri_from_prop).json())
                                self.approved_row(row)
                            else:
                                self.warning_row(row, reason="URI is not a profile")
                        else:
                            self.warning_row(row, reason="URI is not valid")
                self.remove_checked_rows()
            except Exception as e:
                logger.error(f"Error while getting conformsTo uris: {e}")

    def get_type_json_file(self,uri):
        '''
        this function will get the json file from a uri and look into the jsonfile
        @graph [] for @id ./ and check if the @type is an array and if it is check if it contain Profile or Dataset
        :param uri: the uri to the json file    
        :return: the type of the json file
        '''
        logger.info("Getting type of json file")
        try:
            #get the json file
            json_data = get_url(uri).json()
            #checj in the json data if it is a profile
            if is_profile(json_data):
                return "profile"
            
            #check if the json file has conformsTo prop
            if has_conformsTo_prop(json_data):
                #check if the conformsTo prop is an array
                return "crate"
            
            #if none of the above are true then it is json that can't be parsed by this script yet
            logger.warning(f"Json file {uri} is not a profile or a crate")
            return "error"
        except Exception as e:
            logger.error(f"Error while getting type of json file: {e}")
            return "error"
    
    def approved_row(self, row):
        logger.debug(f"Approving row {row}")
        #change the row so that contact => contact.get_contact()
        row["contact"] = row["contact"].get_contact()
        self.checked_rows.append(row)
        self.profile_registry_array.append(row)
    
    def warning_row(self, row, reason):
        logger.debug(f"Warning row {row}")
        row["contact"] = row["contact"].get_contact()
        row["reason"] = reason
        self.checked_rows.append(row)
        self.warnings_rows.append(row)
        
    def failed_row(self, row, reason):
        logger.debug(f"Failed row {row}")
        row["contact"] = row["contact"].get_contact()
        row["reason"] = reason
        self.checked_rows.append(row)
        self.error_rows.append(row)
    
    def remove_checked_rows(self):
        logger.info("Removing checked rows")
        for row in self.checked_rows:
            try:
                self.to_check_rows.remove(row)
            except Exception as e:
                logger.debug(f"Error while removing row: {row})")
                #logger.error(f"Error while removing checked rows: {e}")
                continue
    
    def get_metadata_profiles(self):
        logger.info("Getting metadata profiles")
        for row in self.profile_registry_array:
            try:
                self.knowledge_graph_registry.addProfile(row["URI"])
                metadata = get_metadata_profile(get_url(row["URI"]).json())
                row["metadata"] = metadata
            except Exception as e:
                logger.error(f"Error while getting metadata profiles: {e}")
                logger.exception(e)
                continue
    
    def make_html_file_registry(self):
        logger.info("Making html file")
        try:
            kwargs = {
                "title": "Test Profile registry",
                "description": "This is a test profile registry",
                "theme": "main",
                "datasets": self.registry_json_format
            }
            html_file = make_html_file("index_registry.html",**kwargs)
            #write the html file to the build folder
            with open(os.path.join(Location().get_location(), "build", "index.html"), "w") as f:
                f.write(html_file)
        except Exception as e:
            logger.error(f"Error while making html file: {e}")
            logger.exception(e)
            return False      