#this utility file will contain all functions that will be used to check the csv contact property
from utils.singleton.logger import get_logger
import re

logger = get_logger()

#define a class that will represent a single contact of a row in the csv file 
class Contact():
    def __init__(self, contact):
        logger.debug(f"Creating contact object with contact: {contact}")
        #trim the leading and trailing whitespaces of the contact
        contact = contact.strip()
        self.contact = contact
        self.contact_type = None
        self.contact_result = False
        self.check_type()
        
    def result(self):
        return self.contact_result
    
    def get_contact_type(self):
        return self.contact_type
    
    def get_contact(self):
        return self.contact
    
    def check_type(self):
        '''
        check if the contact is a mail or a orcid (orcid being a url with the following pattern: https://orcid.org/0000-0001-7414-8743)
        '''
        logger.debug(f"Checking type of contact: {self.contact}")
        if re.match(r"[^@]+@[^@]+\.[^@]+", self.contact):
            self.contact_type = "mail"
            self.contact_result = True
            logger.debug(f"Contact is a mail: {self.contact}")
        elif re.match(r"https://orcid.org/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}", self.contact):
            self.contact_type = "orcid"
            self.contact_result = True
            logger.debug(f"Contact is an orcid: {self.contact}")
        else:
            logger.warning(f"Contact is neither a mail nor an orcid: {self.contact}")
            self.contact_result = False
        return self.contact_result
    
    
        
        
            
        
    