from django.utils import simplejson as json

from data_import.lib import BaseReader, BaseWriter, JSONWriter, XMLWriter

## classes of "DOM" elements

class Sitting(object):
    def __init__(self, call=None, date=None, seq_n=None):
        # sitting instance attributes
        self.call = call         
        self.date =  date
        self.seq_n = seq_n
        # ballots comprising this sitting
        self.ballots = []


class Ballot(object):
    def __init__(self, sitting, seq_n=None, timestamp=None, ballot_type=None, 
                 n_presents=None, n_partecipants=None, n_yes=None, n_no=None, n_abst=None, 
                 n_legal=None, outcome=None):
        # parent sitting
        self.sitting = sitting
        # ballot instance attributes
        self.seq_n = seq_n 
        self.time = timestamp
        self.type_ = ballot_type
        self.n_presents = n_presents
        self.n_partecipants = n_partecipants
        self.n_yes = n_yes
        self.n_no = n_no
        self.n_abst = n_abst
        self.n_legal = n_legal
        self.outcome = outcome
        # votes comprising this ballot
        self.votes = []
        

class Vote(object):
    def __init__(self, ballot, cardID=None, componentID=None, groupID=None, choice=None):
        # parent ballot
        self.ballot = ballot
        # vote instance attributes
        self.cardID = cardID 
        self.componentID = componentID
        self.groupID = groupID
        self.choice = choice


class BaseVotationReader(BaseReader):
    """
    An abstract reader class parsing votation-related data.
    
    This class encapsulates generic -- but votation-specific -- parsing logic. 
    It's intended to be subclassed (and its methods overriden) in order to adapt to 
    concrete scenarios. 
    """
    def read(self):
        # initialize the reader
        self.setup()
        
        for sitting in self.get_sittings():
            sitting.ballots = self.get_ballots(sitting)
            for ballot in sitting.ballots:
                ballot.votes = self.get_votes(ballot)
        
        # as now, ``self.sittings`` should be a object tree 
        # providing a comprehensive representation of all relevant data
        # that can be extracted from the data source
        return self.sittings       
    
    def get_sittings(self):
        """
        Retrieve a list comprising all sittings provided by the data source.
        """  
        raise NotImplementedError
    
    def get_ballots(self, sitting):
        """
        Retrieve a list comprising all ballots of a given sitting.
        """
        raise NotImplementedError
    
    def get_votes(self, ballot):
        """
        Retrieve a list comprising all votes of a given ballot.
        """
        raise NotImplementedError

    
class GenericVotationReader(BaseVotationReader):
    pass


class BaseVotationWriter(BaseWriter):
    """
    An abstract writer class that serializes internal representations 
    of votation-related data.
    
    This class encapsulates votation-specific serialization logic which is independent 
    from a specific output format. 
    """
    def __init__(self, sittings):
        self.sittings = sittings

    
class JSONVotationWriter(BaseVotationWriter, JSONWriter):
    """
    A writer class which outputs votations data as a JSON data structure.
    
    Useful for testing purposes. 
    """
    def write(self):
        return json.dumps(self.sittings)
    

class XMLVotationWriter(BaseVotationWriter, XMLWriter):
    """
    A writer class which outputs votations data as a XML document, 
    according to the OM-XML schema specs.
    
    So, its output can be imported directly into a running instance of OpenMunicipio.
    """
    raise NotImplementedError