from django.utils import simplejson as json
from django.core.exceptions import ImproperlyConfigured

import logging

def valid_XML_char_ordinal(i):
    """
    Return when a character is a valid XML char,
    according to http://www.w3.org/TR/2008/REC-xml-20081126/#charsets
    """
    return ( # conditions ordered by presumed frequency
             0x20 <= i <= 0xD7FF
             or i in (0x9, 0xA, 0xD)
             or 0xE000 <= i <= 0xFFFD
             or 0x10000 <= i <= 0x10FFFF
    )

class DataSource(object):
    """
    An object representing a generic source of data.
    
    In this context, the meaning of *data source* is intentionally left very generic: 
    a data source may be a file, a directory of files, a URL, a generic stream, etc.
    
    A concrete data source should expose an API providing easy access to the data
    it contains.  
    """
    
    logger = logging.getLogger('import')
    
    def setup(self):
        """
        Initializes the data source; what this means in practice is strictly
        implementation-dependent.
        """
        pass
    

class BaseReader(object):
    """
    Reads from a data source and returns a parsed, internal representation of the data
    contained within that source.
    
    This an abstract base class, encapsulating generic parsing logic. 
    It's intended to be subclassed (and its methods overriden) in order to adapt to 
    concrete scenarios.    
    """
    
    logger = logging.getLogger('import')
    
    def __init__(self, data_source=None):
        self.data_source = data_source
    
    def setup(self):
        """
        Reader's initialization code goes here.
        """
        pass
    
    def get_data_source(self):
        """
        Returns the data source to read from. 
        
        This base implementation returns the ``data_source`` instance attribute, if set;
        otherwise, raises an ``ImproperlyConfigured`` exception. 
        """   
        try:
            return self.data_source
        except AttributeError:
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
    
    logger = logging.getLogger('import')
    
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
    A writer class which outputs provided data as an XML document. 
    """
    def _set_element_attrs(self, el, attrs):
        """
        Take a tree ``Element`` and a dictionary; set element attributes according
        to that dictionary.
        
        Since attributes names/value MUST be strings, dictionary keys/values are passed 
        through the ``str()`` function.        
        """
        for attname in attrs: 
            el.set(str(attname), str(attrs[attname]))

    def write(self):
        raise NotImplementedError
    
class OMWriter(BaseWriter):
    """
    A writer class which outputs provided data as an OM objects. 
    """
    def write(self):
        raise NotImplementedError