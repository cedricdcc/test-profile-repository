#this file contains a singleton class that will hold the location of src folder
#this is used to make sure that the location of src folder is only set once
import os

def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        #log.debug(f"getting instance of {class_}with args == {args} && kwargs == {kwargs}")
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance

@singleton
class Location():
    def __init__(self, root=None):
        self.root=root
    
    def __repr__(self) -> str:
        return f"Location(root={self.root})"
    
    def get_location(self):
        return self.root