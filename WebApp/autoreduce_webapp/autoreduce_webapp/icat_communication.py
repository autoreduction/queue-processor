from settings import LOG_FILE, LOG_LEVEL, ICAT, BASE_DIR
import logging, os, sys, datetime
logger = logging.getLogger(__name__)
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
        logger.debug("Logging in to ICAT at %s" % kwargs['URL'])
        self.client = icat.Client(url=kwargs['URL'])
        self.sessionId = self.client.login(kwargs['AUTH'], kwargs['SESSION'])
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        logger.debug("Logging out of ICAT")
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
        logger.debug("Calling ICATCommunication.get_experiment_details")
        if not isinstance(reference_number, (int, long)):
            raise TypeError("Reference number must be a number")

        if reference_number > 0:
            try:
                investigation = self.client.search("SELECT i from Investigation i where i.name = '" + str(reference_number) + "' INCLUDE i.investigationInstruments.instrument, i.investigationUsers.user")
                
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
                
            except:
                pass
                
        trimmed_investigation = {
            'reference_number' : str(reference_number),
            'start_date' : 'N/A',
            'end_date' : 'N/A',
            'title' : 'N/A',
            'summary' : u'N/A',
            'pi' : ''
            }

        return trimmed_investigation

    '''
        Returns a set of all instruments a given user can see.
        This includes instruments they own and are an experimenter on.
    '''
    def get_valid_instruments(self, user_number):
        logger.debug("Calling ICATCommunication.get_valid_instruments")
        if not isinstance(user_number, (int, long)):
            raise TypeError("User number must be a number")

        instruments = Set()
        if self.is_admin(user_number):
            self._add_list_to_set(self.client.search("SELECT inst.fullName FROM Instrument inst"), instruments)
        else:
            self._add_list_to_set(self.get_owned_instruments(user_number), instruments)
            self._add_list_to_set(self.client.search("SELECT inst.fullName FROM Instrument inst JOIN inst.investigationInstruments ii WHERE ii.investigation.id IN (SELECT i.id from Investigation i JOIN i.investigationUsers iu WHERE iu.user.name = 'uows/" + str(user_number) + "')"), instruments)
        return sorted(instruments)

    '''
        Returns all instruments for which the given user is an instrument scientist
    '''
    def get_owned_instruments(self, user_number):
        logger.debug("Calling ICATCommunication.get_owned_instruments")
        if not isinstance(user_number, (int, long)):
            raise TypeError("User number must be a number")

        instruments = Set()
        self._add_list_to_set(self.client.search("SELECT ins.instrument.fullName from InstrumentScientist ins WHERE ins.user.name = 'uows/" + str(user_number) + "'"), instruments)
        return sorted(instruments)

    '''
        Checks if a user has any owned instruments and thus an instrument scientist
    '''
    def is_instrument_scientist(self, user_number):
        logger.debug("Calling ICATCommunication.is_instrument_scientist")
        if self.get_owned_instruments(user_number):
            return True
        return False

    '''
        Returns True is the given user is part of the experiment team for the given reference number.
    '''
    def is_on_experiment_team(self, reference_number, user_number):
        logger.debug("Calling ICATCommunication.is_on_experiment_team")
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
        logger.debug("Calling ICATCommunication.get_associated_experiments")
        if not isinstance(user_number, (int, long)):
            raise TypeError("User number must be a number")

        experiments = Set()
        self._add_list_to_set(self.client.search("SELECT i.name from Investigation i JOIN i.investigationUsers iu where iu.user.name = 'uows/" + str(user_number) + "'"), experiments)
        return sorted(experiments, reverse=True)

    '''
        Returns all experiments allowed for a given list of instruments
    '''
    def get_valid_experiments_for_instruments(self, user_number, instruments):
        logger.debug("Calling ICATCommunication.get_valid_experiments_for_instruments")
        from reduction_viewer.models import Setting
        if not isinstance(user_number, (int, long)):
            raise TypeError("User number must be a number")
        if not instruments:
            raise Exception("At least one instrument must be supplied")

        instruments_dict = {}

        try:
            number_of_years = int(Setting.objects.get(name='ICAT_YEARS_TO_SHOW').value)
        except:
            number_of_years = 3
        years_back = datetime.datetime.now() - datetime.timedelta(days=(number_of_years*365.24))

        for instrument in instruments:
            experiments = Set()
            self._add_list_to_set(self.client.search("SELECT i.name FROM Investigation i JOIN i.investigationInstruments inst WHERE i.name NOT LIKE 'CAL%' and i.endDate > '"+str(years_back)+"' and (inst.instrument.name = '"+instrument+"' OR inst.instrument.fullName = '"+instrument+"')"), experiments)
            instruments_dict[instrument] = sorted(experiments, reverse=True)

        return instruments_dict

    '''
        Returns all experiments allowed for a given instrument
    '''
    def get_valid_experiments_for_instrument(self, instrument):
        logger.debug("Calling ICATCommunication.get_valid_experiments_for_instrument")
        from reduction_viewer.models import Setting

        try:
            number_of_years = int(Setting.objects.get(name='ICAT_YEARS_TO_SHOW').value)
        except:
            number_of_years = 3
        years_back = datetime.datetime.now() - datetime.timedelta(days=(number_of_years*365.24))

        experiments = Set()
        self._add_list_to_set(self.client.search("SELECT i.name FROM Investigation i JOIN i.investigationInstruments inst WHERE i.name NOT LIKE 'CAL%' and i.endDate > '"+str(years_back)+"' and (inst.instrument.name = '"+instrument+"' OR inst.instrument.fullName = '"+instrument+"')"), experiments)
        return sorted(experiments, reverse=True)

    def get_upcoming_experiments_for_instrument(self, instrument):
        logger.debug("Calling ICATCommunication.get_upcoming_experiments_for_instrument")
        if not instrument:
            raise Exception("At least one instrument must be supplied")

        experiments = Set()
        self._add_list_to_set(self.client.search("SELECT i.name FROM Investigation i JOIN i.investigationInstruments inst WHERE i.name NOT LIKE 'CAL%' and i.endDate > CURRENT_TIMESTAMP and (inst.instrument.name = '"+instrument+"' OR inst.instrument.fullName = '"+instrument+"')"), experiments)
        return sorted(experiments, reverse=True)

    '''
        Check if the user is in the relevant admin group within ICAT for the autoreduction webapp
    '''
    def is_admin(self, user_number):
        logger.debug("Calling ICATCommunication.is_admin")
        admin_group = 'Autoreduce Admins'
        if self.client.search("SELECT g FROM Grouping g JOIN g.userGroups ug WHERE g.name = '"+ admin_group +"' and ug.user.name = 'uows/"+ str(user_number) +"'"):
            return True
        return False

    '''
        Return a list of runs from ICAT given a start and end run number
    '''
    def get_run_details(self, instrument, start_run_number, end_run_number):
        logger.debug("Calling ICATCommunication.get_run_details")
        if not instrument:
            raise Exception("At least one instrument must be supplied")
        if not start_run_number:
            raise Exception("At least one run_number must be supplied")
        if not end_run_number:
            raise Exception("At least one run_number must be supplied")

        return self.client.search("SELECT dfp FROM DatafileParameter dfp JOIN dfp.datafile.dataset.investigation.investigationInstruments ii WHERE dfp.type.name='run_number' and dfp.numericValue >= "+str(start_run_number)+" and dfp.numericValue <= "+str(end_run_number)+" and ii.instrument.fullName = '"+instrument+"' and dfp.datafile.dataset.investigation.name not LIKE 'CAL%%' include dfp.datafile.dataset.investigation")

    '''
        Performs any post-processing actions required once reduction is complete.
        Currenty a placeholder. Not sure yet what this may contain.
    '''
    def post_process(self, reduction_run):
        logger.debug("Calling ICATCommunication.post_process")
        # TODO: ICAT post-processing
        pass