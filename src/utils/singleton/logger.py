import logging
import inspect
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
            
def get_logger():
    # Get the name of the calling module
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    module_name = module.__name__

    # Create a logger instance with the module name as its name
    logger = SingletonLogger(module_name)
    return logger