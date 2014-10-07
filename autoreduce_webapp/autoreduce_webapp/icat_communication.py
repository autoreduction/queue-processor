from settings import LOG_FILE, LOG_LEVEL, ICAT, BASE_DIR
import logging, os, sys, datetime
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
from sets import Set
import icat
sys.path.insert(0, BASE_DIR)

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

    def _build_in_clause(self, field, values):
        clause = field + " IN ("
        for item in values:
            if isinstance(item, (int, long)):
                clause += "" + str(item) + ","
            else:
                clause += "'" + str(item) + "',"
        clause = clause[:-1] + ")"
        return clause

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
        Checks if a user has any owned instruments and thus an instrument scientist
    '''
    def is_instrument_scientist(self, user_number):
        if self.get_owned_instruments(user_number):
            return True
        return False

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
        Returns all experiments allowed for a given list of instruments
    '''
    def get_valid_experiments_for_instruments(self, user_number, instruments):
        from reduction_viewer.models import Setting
        if not isinstance(user_number, (int, long)):
            raise TypeError("User number must be a number")
        if not instruments:
            raise Exception("At least one instrument must be supplied")

        instruments_dict = {}

        number_of_years = Setting.objects.filter(name='ICAT_YEARS_TO_SHOW')
        if not number_of_years:
            number_of_years = 3
        years_back = datetime.datetime.now() - datetime.timedelta(days=(number_of_years*365.24))

        for instrument in instruments:
            experiments = Set()
            self._add_list_to_set(self.client.search("SELECT i.name FROM Investigation i JOIN i.investigationInstruments inst WHERE i.endDate > '"+str(years_back)+"' and inst.instrument.name = '"+instrument+"' INCLUDE i.investigationInstruments.instrument"), experiments)
            instruments_dict[instrument] = experiments

        return instruments_dict

    '''
        Check if the user is in the relevant admin group within ICAT for the autoreduction webapp
    '''
    def is_admin(self, user_number):
        admin_group = 'Autoreduce Admins'
        if self.client.search("SELECT g FROM Grouping g JOIN g.userGroups ug WHERE g.name = '"+ admin_group +"' and ug.user.name = 'uows/"+ str(user_number) +"'"):
            return True
        return False

    '''
        Performs any post-processing actions required once reduction is complete.
        Currenty a placeholder. Not sure yet what this may contain.
    '''
    def post_process(self, reduction_run):
        # TODO: ICAT post-processing
        pass