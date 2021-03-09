# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Deals with communication with ICAT service
"""
import datetime
import logging
import os
import sys

import icat
from django.utils.encoding import smart_str

from utils.project.structure import get_project_root
# The below is a template on the repository
from .settings import ICAT, BASE_DIR

sys.path.append(os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp'))

from reduction_viewer.models import Setting

LOGGER = logging.getLogger(__name__)
sys.path.insert(0, BASE_DIR)


class ICATCommunication:
    """
    Handles communication with the ICAT service
    """
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
            kwargs['SESSION'] = {'username': kwargs['USER'], 'password': kwargs['PASSWORD']}
            LOGGER.debug("Logging in to ICAT at %s", kwargs['URL'])
        self.client = icat.Client(url=kwargs['URL'])
        # pylint: disable=invalid-name
        self.sessionId = self.client.login(kwargs['AUTH'], kwargs['SESSION'])

    def __enter__(self):
        return self

    # pylint: disable=redefined-builtin
    def __exit__(self, type, value, traceback):
        LOGGER.debug("Logging out of ICAT")
        self.client.logout()

    @staticmethod
    def _add_list_to_set(my_list, my_set):
        """
        Takes all items in the given list and adds them to the given set
        """
        my_set = [my_set.add(each) for each in my_list]
        return my_set

    def get_experiment_details(self, reference_number):
        """
        Returns experiment details for the given reference number
        """
        LOGGER.debug("Calling ICATCommunication.get_experiment_details")
        if not isinstance(reference_number, int):
            raise TypeError("Reference number must be a number")

        if reference_number > 0:
            try:
                investigation = self.client.search("SELECT i from Investigation i where i.name = '" +
                                                   str(reference_number) + "' INCLUDE i.investigationInstruments."
                                                   "instrument, i.investigationUsers.user")

                trimmed_investigation = {
                    'reference_number': investigation[0].name,
                    'start_date': investigation[0].startDate,
                    'end_date': investigation[0].endDate,
                    'title': smart_str(investigation[0].title),
                    'summary': smart_str(investigation[0].summary),
                    'instrument': investigation[0].investigationInstruments[0].instrument.fullName,
                    'pi': ''
                }

                for investigation_user in investigation[0].investigationUsers:
                    if investigation_user.role == 'principal_experimenter':
                        trimmed_investigation['pi'] = smart_str(investigation_user.user.fullName)
                return trimmed_investigation
            # pylint: disable=bare-except
            except:
                pass

        trimmed_investigation = {
            'reference_number': str(reference_number),
            'start_date': 'N/A',
            'end_date': 'N/A',
            'title': 'N/A',
            'summary': u'N/A',
            'pi': ''
        }

        return trimmed_investigation

    def get_valid_instruments(self, user_number):
        """
        Returns a set of all instruments a given user can see.
        This includes instruments they own and are an experimenter on.
        """
        LOGGER.debug("Calling ICATCommunication.get_valid_instruments")
        if not isinstance(user_number, int):
            raise TypeError("User number must be a number")

        instruments = set()
        if self.is_admin(user_number):
            self._add_list_to_set(self.client.search("SELECT inst.fullName FROM Instrument inst"), instruments)
        else:
            self._add_list_to_set(self.get_owned_instruments(user_number), instruments)
            self._add_list_to_set(
                self.client.search("SELECT inst.fullName FROM Instrument inst"
                                   " JOIN inst.investigationInstruments ii"
                                   " WHERE ii.investigation.id IN"
                                   " (SELECT i.id from Investigation i JOIN"
                                   " i.investigationUsers iu WHERE"
                                   " iu.user.name = 'uows/" + str(user_number) + "')"), instruments)
        return sorted(instruments)

    def get_owned_instruments(self, user_number):
        """
        Returns all instruments for which the given user is an instrument scientist
        """
        LOGGER.debug("Calling ICATCommunication.get_owned_instruments")
        if not isinstance(user_number, int):
            raise TypeError("User number must be a number")

        instruments = set()
        self._add_list_to_set(
            self.client.search("SELECT ins.instrument.fullName from"
                               " InstrumentScientist ins WHERE"
                               " ins.user.name = 'uows/" + str(user_number) + "'"), instruments)
        return sorted(instruments)

    def is_instrument_scientist(self, user_number):
        """
        Checks if a user has any owned instruments and thus an instrument scientist
        """
        LOGGER.debug("Calling ICATCommunication.is_instrument_scientist")
        if self.get_owned_instruments(user_number):
            return True
        return False

    def is_on_experiment_team(self, reference_number, user_number):
        """
        Returns True is the given user is part of the experiment team
        for the given reference number.
        """
        LOGGER.debug("Calling ICATCommunication.is_on_experiment_team")
        if not isinstance(user_number, int) or not \
                isinstance(reference_number, int):
            raise TypeError("User number and reference number must be a number")

        is_on_team = self.client.search("SELECT i.name from Investigation i JOIN"
                                        " i.investigationUsers iu where"
                                        " iu.user.name = 'uows/" + str(user_number) + "' and i.name = '" +
                                        str(reference_number) + "'")
        if is_on_team:
            return True
        return False

    def get_associated_experiments(self, user_number):
        """
        Returns a set of experiment reference numbers for which the given
        user is on the experiment team.
        """
        LOGGER.debug("Calling ICATCommunication.get_associated_experiments")
        if not isinstance(user_number, int):
            raise TypeError("User number must be a number")

        experiments = set()
        self._add_list_to_set(
            self.client.search("SELECT i.name from Investigation i JOIN"
                               " i.investigationUsers iu where"
                               " iu.user.name = 'uows/" + str(user_number) + "'"), experiments)
        return sorted(experiments, reverse=True)

    # pylint: disable=invalid-name
    def get_valid_experiments_for_instruments(self, user_number, instruments):
        """
        Returns all experiments allowed for a given list of instruments
        """
        LOGGER.debug("Calling ICATCommunication.get_valid_experiments_for_instruments")
        if not isinstance(user_number, int):
            raise TypeError("User number must be a number")
        if not instruments:
            raise Exception("At least one instrument must be supplied")

        instruments_dict = {}

        try:
            # pylint: disable=no-member
            number_of_years = int(Setting.objects.get(name='ICAT_YEARS_TO_SHOW').value)
        # pylint: disable=bare-except
        except:
            number_of_years = 3
        years_back = datetime.datetime.now() - datetime.timedelta(days=(number_of_years * 365.24))

        for instrument in instruments:
            experiments = set()
            self._add_list_to_set(
                self.client.search("SELECT i.name FROM Investigation i"
                                   " JOIN i.investigationInstruments inst"
                                   " WHERE i.name NOT LIKE 'CAL%' and"
                                   " i.endDate > '" + str(years_back) + "' and (inst.instrument.name = '" + instrument +
                                   "' OR inst.instrument.fullName = '" + instrument + "')"), experiments)

            instruments_dict[instrument] = sorted(experiments, reverse=True)

        return instruments_dict

    # pylint: disable=invalid-name
    def get_valid_experiments_for_instrument(self, instrument):
        """
        Returns all experiments allowed for a given instrument
        """
        LOGGER.debug("Calling ICATCommunication.get_valid_experiments_for_instrument")

        try:
            # pylint: disable=no-member
            number_of_years = int(Setting.objects.get(name='ICAT_YEARS_TO_SHOW').value)
        # pylint: disable=bare-except
        except:
            number_of_years = 3
        years_back = datetime.datetime.now() - datetime.timedelta(days=(number_of_years * 365.24))

        experiments = set()
        self._add_list_to_set(
            self.client.search("SELECT i.name FROM Investigation i JOIN"
                               " i.investigationInstruments inst WHERE"
                               " i.name NOT LIKE 'CAL%' and i.endDate > '" + str(years_back) +
                               "' and (inst.instrument.name = '" + instrument + "' OR inst.instrument.fullName = '" +
                               instrument + "')"), experiments)
        return sorted(experiments, reverse=True)

    # pylint: disable=invalid-name
    def get_upcoming_experiments_for_instrument(self, instrument):
        """
        Get the upcoming experiments as expected by ICAT
        """
        LOGGER.debug("Calling ICATCommunication.get_upcoming_experiments_for_instrument")
        if not instrument:
            raise Exception("At least one instrument must be supplied")

        experiments = set()
        self._add_list_to_set(
            self.client.search("SELECT i.name FROM Investigation i JOIN"
                               " i.investigationInstruments inst WHERE"
                               " i.name NOT LIKE 'CAL%' and"
                               " i.endDate > CURRENT_TIMESTAMP and"
                               " (inst.instrument.name = '" + instrument + "' OR inst.instrument.fullName = '" +
                               instrument + "')"), experiments)
        return sorted(experiments, reverse=True)

    def is_admin(self, user_number):
        """
        Check if the user is in the relevant admin group within ICAT for the autoreduction webapp
        """
        LOGGER.debug("Calling ICATCommunication.is_admin")
        admin_group = 'Autoreduce Admins'
        if self.client.search("SELECT g FROM Grouping g JOIN g.userGroups ug WHERE g.name = '" + admin_group +
                              "' and ug.user.name = 'uows/" + str(user_number) + "'"):
            return True
        return False

    def get_run_details(self, instrument, start_run_number, end_run_number):
        """
        Return a list of runs from ICAT given a start and end run number
        """
        LOGGER.debug("Calling ICATCommunication.get_run_details")
        if not instrument:
            raise Exception("At least one instrument must be supplied")
        if not start_run_number:
            raise Exception("At least one run_number must be supplied")
        if not end_run_number:
            raise Exception("At least one run_number must be supplied")

        return self.client.search("SELECT dfp FROM DatafileParameter dfp JOIN "
                                  "dfp.datafile.dataset.investigation.investigationInstruments "
                                  "ii WHERE dfp.type.name='run_number' and dfp.numericValue >= " +
                                  str(start_run_number) + " and dfp.numericValue <= " + str(end_run_number) +
                                  " and ii.instrument.fullName = '" + instrument +
                                  "' and dfp.datafile.dataset.investigation.name "
                                  "not LIKE 'CAL%%' include "
                                  "dfp.datafile.dataset.investigation")

    @staticmethod
    def post_process(_):
        """
        Performs any post-processing actions required once reduction is complete.
        Currenty a placeholder. Not sure yet what this may contain.

        CURRENTLY NOT IMPLEMETNED
        """
        LOGGER.debug("Calling ICATCommunication.post_process")
