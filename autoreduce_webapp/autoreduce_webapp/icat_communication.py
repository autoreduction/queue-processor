from settings import LOG_FILE, LOG_LEVEL, ICAT
import logging
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
from sets import Set
import icat

class ICATCommunication(object):
    def __init__(self, **kwargs):
        if 'URL' not in kwargs:
            kwargs['URL'] = ICAT['URL']
        if 'AUTH' not in kwargs:
            kwargs['AUTH'] = ICAT['AUTH']
        if 'USER' not in kwargs:
            kwargs['USER'] = ICAT['USER']
        if 'PASSWORD' not in kwargs:
            kwargs['PASSWORD'] = ICAT['PASSWORD']
        if 'SESSION' not in kwargs:
            kwargs['SESSION'] = { 'username' : kwargs['USER'], 'password' : kwargs['PASSWORD']}
        logging.debug("Logging in to ICAT at %s" % kwargs['URL'])
        self.client = icat.Client(url=kwargs['URL'])
        self.sessionId = self.client.login(kwargs['AUTH'], kwargs['SESSION'])
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        logging.debug("Logging out of ICAT")
        self.client.logout()
    
    '''
        Takes all items in the given list and adds them to the given set
    '''
    def _add_list_to_set(self, my_list, my_set):
        [my_set.add(each) for each in my_list]
        return my_set

    '''
        Returns experiment details for the given reference number
    '''
    def get_experiment_details(self, reference_number):
        if not isinstance(reference_number, (int, long)):
            raise TypeError("Reference number must be a number")

        investigation = self.client.search("SELECT i from Investigation i where i.name = '" + str(reference_number) + "' INCLUDE i.investigationInstruments.instrument, i.investigationUsers.user")
        if investigation and investigation[0]:
            trimmed_investigation = {
                'reference_number' : investigation[0].name,
                'start_date' : investigation[0].startDate,
                'end_date' : investigation[0].endDate,
                'title' : investigation[0].title,
                'summary' : u''+investigation[0].summary,
                'instrument' : investigation[0].investigationInstruments[0].instrument.fullName,
                'pi' : ''
            }
            for investigationUser in investigation[0].investigationUsers:
                if investigationUser.role == 'principal_experimenter':
                    trimmed_investigation['pi'] = investigationUser.user.fullName
            return trimmed_investigation
        return None

    '''
        Returns a set of all instruments a given user can see.
        This includes instruments they own and are an experimenter on.
    '''
    def get_valid_instruments(self, user_number):
        if not isinstance(user_number, (int, long)):
            raise TypeError("User number must be a number")

        instruments = Set()
        self._add_list_to_set(self.get_owned_instruments(user_number), instruments)
        self._add_list_to_set(self.client.search("SELECT inst.name FROM Instrument inst JOIN inst.investigationInstruments ii WHERE ii.investigation.id IN (SELECT i.id from Investigation i JOIN i.investigationUsers iu WHERE iu.user.name = 'uows/" + str(user_number) + "')"), instruments)
        return instruments

    '''
        Returns all instruments for which the given user is an instrument scientist
    '''
    def get_owned_instruments(self, user_number):
        if not isinstance(user_number, (int, long)):
            raise TypeError("User number must be a number")

        instruments = Set()
        self._add_list_to_set(self.client.search("SELECT ins.instrument.name from InstrumentScientist ins WHERE ins.user.name = 'uows/" + str(user_number) + "'"), instruments)
        return instruments

    '''
        Returns True is the given user is part of the experiment team for the given reference number.
    '''
    def is_on_experiment_team(self, reference_number, user_number):
        if not isinstance(user_number, (int, long)) or not isinstance(reference_number, (int, long)):
            raise TypeError("User number and reference number must be a number")

        is_on_team = self.client.search("SELECT i.name from Investigation i JOIN i.investigationUsers iu where iu.user.name = 'uows/" + str(user_number) + "' and i.name = '" + str(reference_number) + "'")
        if is_on_team:
            return True
        return False

    '''
        Returns a set of experiment reference numbers for which the given user is on the experiment team.
    '''
    def get_associated_experiments(self, user_number):
        if not isinstance(user_number, (int, long)):
            raise TypeError("User number must be a number")

        experiments = Set()
        self._add_list_to_set(self.client.search("SELECT i.name from Investigation i JOIN i.investigationUsers iu where iu.user.name = 'uows/" + str(user_number) + "'"), experiments)
        return experiments

    '''
        Performs any post-processing actions required once reduction is complete.
        Currenty a placeholder. Not sure yet what this may contain.
    '''
    def post_processing(self, reduction_run):
        pass