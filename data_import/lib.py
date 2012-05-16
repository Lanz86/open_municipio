from django.utils import simplejson as json
from django.core.exceptions import ImproperlyConfigured

class BaseReader(object):
    """
    Reads from a data source and returns a parsed, internal representation of the data
    contained within that source.
    
    This an abstract base class, encapsulating generic parsing logic. 
    It's intended to be subclassed (and its methods overriden) in order to adapt to 
    concrete scenarios. 
    
    In this context, the meaning of *data source* is implementation-dependent: 
    a data source may be a file, a directory of files, a URLs, a generic stream, etc.
    """
    def __init__(self, data_source=None):
        self.data_source = data_source
    
    def setup(self):
        """
        Reader's initialization code goes here.
        """
        pass
    
    def get_data_source(self):
        """
        Return an object representing the data source to read from. 
        
        This base implementation returns the ``data_source`` instance attribute, if set;
        otherwise, raises an ``ImproperlyConfigured`` exception. 
        """   
        if self.data_source:
            return self.data_source
        else:
            raise ImproperlyConfigured("You must provide a data source")  
     
    def read(self):
        raise NotImplementedError
  
    
class BaseWriter(object):
    """
    Serializes a given data structure to a specific output format.
    
    This data structure would usually (but not necessarily) be a tree of Python objects,
    while the output format would be some kind of string representation of that 
    internal data structure.
    
    This an abstract base class, encapsulating generic serialization logic. 
    It's intended to be subclassed (and its methods overriden) in order to 
    provide support for a given serialization format.
    """
    def __init__(self, data):
        self.data = data
        
    def write(self):
        raise NotImplementedError


class JSONWriter(BaseWriter):
    """
    A writer class which outputs provided data as a JSON data structure.
    
    Useful for testing purposes. 
    """
    def write(self):
        return json.dumps(self.data)


class XMLWriter(BaseWriter):
    """
    A writer class which outputs provided data as a XML document. 
    """
    raise NotImplementedError