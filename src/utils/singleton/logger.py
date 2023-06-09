import logging
import inspect
import os
from utils.singleton.location import Location
class SingletonLogger(logging.Logger):
    _instance = None
    __initialized = False
    def __init__(self, name=None, level=logging.DEBUG):
        if not self.__initialized:
            self.__initialized = True
            super().__init__(name=name, level=level)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s  - %(message)s')
            console_handler.setFormatter(formatter)
            self.addHandler(console_handler)
            #add file to log to
            file_handler = logging.FileHandler('logs.log')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)
    
def get_warnings_log():
    '''
    this function will return the warnings logs that are in the logs.log file
    '''
    
    with open(os.path.join(Location().get_location(), "logs.log"), "r") as f:
        #get the logs
        logs = f.readlines()
    #filter the logs to get only the warnings
    warnings = list(filter(lambda log: "WARNING" in log, logs))
    return warnings

def get_errors_log():
    '''
    this function will return the errors logs that are in the logs.log file
    '''
    with open(os.path.join(Location().get_location(), "logs.log"), "r") as f:
        #get the logs
        logs = f.readlines()
    #filter the logs to get only the warnings
    errors = list(filter(lambda log: "ERROR" in log, logs))
    return errors
            
def get_logger():
    # Get the name of the calling module
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    module_name = module.__name__

    # Create a logger instance with the module name as its name
    logger = SingletonLogger(module_name)
    return logger

