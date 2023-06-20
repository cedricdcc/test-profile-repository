#this file will contain all the functions that will be used to build the registry that will be used to build the gh-pages
import os
import csv
import json
import rdflib
from utils.singleton.location import Location
from utils.singleton.logger import get_logger, get_warnings_log
from utils.uri_checks import check_uri, check_if_json_return, get_url, check_uri_content
from utils.jsonld_file import has_conformsTo_prop, get_cornformTo_uris, is_profile, get_profile_prop, get_metadata_profile
from utils.html_build_util import make_html_file, setup_build_folder
from utils.rdflib_utils import KnowledgeGraphRegistry
from utils.contact import Contact
from utils.profileharvester import ProfileHarvester
logger = get_logger()

#registry class that will hold the registry
class Registry():
    def __init__(self, data_path, registry=None):
        self.registry = registry
        self.entry_errors = []
        self.entry_warnings = []
        self.to_check_rows = []
        self.checked_rows = []
        self.data_path = data_path
        self.profile_registry_array = []
        self.knowledge_graph_registry = KnowledgeGraphRegistry(base="test",knowledgeGraph=None)
    
    def __repr__(self) -> str:
        return f"Registry(registry={self.registry})"
    
    def report(self):
        logger.info("Generating report")
        report = {}
        report["entry_errors"] = self.entry_errors
        report["entry_warnings"] = self.entry_warnings
        report["to_check_rows"] = self.to_check_rows
        report["checked_rows"] = self.checked_rows
        report["profile_registry_array"] = self.profile_registry_array
        logger.debug(report["to_check_rows"])
        '''
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
        '''
        return report
        
        
    
    def get_registry(self):
        return self.registry
    
    def build(self):
        '''
        this function will build the registry
        :param data_path: the path to the data folder
        :return: the registry
        '''
        
        logger.info("Building registry")
        #function here to detect all the csv files in the data_path including subfolders
        self.csv_files = self.detect_csv_files()
        logger.info(f"Found {len(self.csv_files)} csv files")
        #function that will go over all the csv files and return an array of dictionaries with each entry in the array being {"source": "relative path to csv file", "URI": "URI of a given profile", "contact":"contact" }
        self.registry_array = self.make_entries_array()
        self.entries_array_check()
        self.entries_harvestor()
        #self.get_metadata_profiles()
        setup_build_folder()
        self.knowledge_graph_registry.toTurtle()
        #write the knowledge graph to a ttl file
        self.registry_json_format = self.knowledge_graph_registry.extractMetadata()
        self.make_html_file_registry()

    def detect_csv_files(self):
        '''
        this function will detect all the csv files in the data_path including subfolders
        :param data_path: the path to the data folder
        :return: the list of csv files
        '''
        logger.info("Detecting csv files")
        csv_files = []
        for root, dirs, files in os.walk(self.data_path):
            for file in files:
                if file.endswith(".csv"):
                    csv_files.append(os.path.join(root, file))
        return csv_files
    
    def entries_harvestor(self):
        '''
        This function will make a harvestor class for each entry in the registry_array.
        '''
        logger.info("Making harvestors")
        self.profile_metadate_dicts = {}
        for entry in self.to_check_rows:
            logger.info(f"Making harvestor for {entry['URI']}")
            entry_harvestor = ProfileHarvester(entry["URI"])
            entry_harvestor.harvest()
            entry["harvestor"] = entry_harvestor
            logger.debug(entry_harvestor.get_kg())
            logger.info(f"Harvestor for {entry['URI']} has run")
            logger.info(f"Harvester has found {len(entry_harvestor.getProfiles())} profiles")
            logger.debug(entry_harvestor.getCompleteKG().serialize(format = "turtle", base=entry['URI'], encoding="utf-8").decode("utf-8"))
            logger.info(f"Harvestor for {entry['URI']} has run")
            harvested_info = entry_harvestor.getListDictsProfiles()
            #ppritn the harvested info
            logger.info(json.dumps(harvested_info, indent=4))
            self.profile_metadate_dicts.update(harvested_info)
    
    def make_entries_array(self):
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
    
    def entries_array_check(self):
        '''
        this function will make the registry
        :param registry_array: the array of dictionaries
        :return: the registry
        '''
        logger.info("Checking registry array")
        for entry in self.registry_array:
            #first check if the contact is valid
            good = True
            logger.debug(f"Checking contact {entry['contact'].get_contact()}")
            if not entry["contact"].result():
                self.entry_warning(entry, reason="Contact is not valid")
                good = False
            logger.info(f"Checking entry {entry}")
            #check if the URI is valid
            #check if the URI is already in the registry
            for row  in self.to_check_rows:
                if entry["URI"] == row["URI"]:
                    self.entry_warning(entry, reason="URI is already in registry")
                    good = False
                    break
            if not check_uri(entry["URI"]):
                self.entry_failed(entry, reason="URI is not valid")
                good = False
            #check if the URI return a valid json-ld
            if good:
                self.to_check_rows.append(entry)     
    
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
                "datasets": self.profile_metadate_dicts
            }
            html_file = make_html_file("index_registry.html",**kwargs)
            #write the html file to the build folder
            with open(os.path.join(Location().get_location(), "build", "index.html"), "w") as f:
                f.write(html_file)
        except Exception as e:
            logger.error(f"Error while making html file: {e}")
            logger.exception(e)
            return False      
    
    def entry_warning(self, entry, reason):
        uri = entry["URI"]
        logger.warning(f"Entry {uri} is not valid because {reason}")
        self.entry_warnings.append(entry)
    
    def entry_failed(self, entry, reason):
        uri = entry["URI"]
        logger.error(f"Entry {uri} is not valid because {reason}")
        self.entry_errors.append(entry)