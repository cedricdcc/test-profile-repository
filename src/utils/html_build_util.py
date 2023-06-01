#file that contains function to help build and clean build folder

import os
import sys
import shutil
from utils.singleton import location
from utils.singleton.logger import get_logger
from jinja2 import Template

logger = get_logger()

def setup_build_folder():
    '''
    this function will setup the build folder
    '''
    # check if the build folder exists
    logger.info("Setting up build folder")
    logger.debug(location.Location().get_location())
    if not os.path.isdir(os.path.join(location.Location().get_location(), "build")):
        os.mkdir(os.path.join(location.Location().get_location(), "build"))
    else:
        # if it exists, clean it
        clean_build_folder()
        
def clean_build_folder():
    if os.path.isdir(os.path.join(location.Location().get_location(), "build")):
        for file in os.listdir(os.path.join(location.Location().get_location(), "build")):
            try:
                shutil.rmtree(os.path.join(os.path.join(location.Location().get_location(), "build"), file))
            except NotADirectoryError:
                os.remove(os.path.join(os.path.join(location.Location().get_location(), "build"), file))
    else:
        logger.error("{} folder does not exist", os.path.join(location.Location().get_location(), "build"))
        sys.exit(1)
        
#template file here to make html files
def make_html_file(template_file, **kwargs):
    '''
    this function will make the html file
    :param template_file: the template file to use
    :param kwargs: the arguments to pass to the template file
    :return: the html file
    '''
    logger.info("Making html file")
    logger.debug(location.Location().get_location())
    # check if the build folder exists
    if not os.path.isdir(os.path.join(location.Location().get_location(), "build")):
        logger.error("Build folder does not exist")
        sys.exit(1)
    # check if the template file exists
    if not os.path.isfile(os.path.join(location.Location().get_location(), "templates", template_file)):
        logger.error("Template file does not exist")
        sys.exit(1)
    # check if the html file exists
    if os.path.isfile(os.path.join(location.Location().get_location(), "build", template_file)):
        logger.error("Html file already exists")
        sys.exit(1)
    # read the template file
    try:
        template = Template(open(os.path.join(location.Location().get_location(), "templates", template_file)).read())
        # render the template file
        html = template.render(**kwargs)
    except Exception as e:
        logger.error("Error rendering template file: {}".format(e))
        logger.debug("Error rendering template file: {}".format(e), exc_info=True)
        sys.exit(1)
    return html