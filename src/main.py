# main file component
# This file is the main file of the project. It contains the main function
# This file will distribute the work to other files
# first thing is to check the given config file and load it
# based on config file, it will make the necessary calls to other files and make folders for the output files
import os
import sys
import yaml
from utils.singleton.location import Location
from utils.singleton.logger import get_logger

logger = get_logger()
# set the location of the src folder
Location(root=os.path.dirname(os.path.abspath(__file__)))

# check if the data folder exists
if not os.path.isdir("data"):
    logger.error("Data folder not found. Please make sure it exists in src/data")
    sys.exit(1)

build_gh_pages(config, os.path.join(Location().get_location(), "data"))