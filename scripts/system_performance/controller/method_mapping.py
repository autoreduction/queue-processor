# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Handles User input (N instruments, N methods and N additional method arguments), mapping
user specified methods formatted as strings to their corresponding method in controller applying
any additional arguments specified.

:returns a dictionary of dictionaries containing statistics per instrument, per method
"""

# Dependencies
import logging

from scripts.system_performance.controller.statistics_computation import QueryHandler
from scripts.system_performance.models import query_argument_constructor


class MethodSelectorConfigurator:
    """ Logic to call method specified by user for N instruments +
        any additional method arguments specified for method."""

    @staticmethod
    def create_method_mappings():
        """ Dictionary to map input, user specified methods to return equivalent method to be
            called
             =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :returns:
            ----------
            - dictionary: Contains dictionary of methods that can be used in package, acting as a
            form of method validation"""

        return {'missing_run_numbers_report': QueryHandler().missing_run_numbers_report,
                'execution_times': QueryHandler().execution_times,
                # 'execution_time_average': self.execution_time_average, TODO create method
                'run_frequency': QueryHandler().run_frequency,
                # 'run_frequency_average': self.run_frequency_average _ TODO create method
                }

    def method_call(self, method_name, method_args):
        """ Calls user specified method and returns statistics for a given instrument
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - method_name (string): The name of method to map to method object.
            - method_args (dictionary): Dictionary containing method args to be passed to mapped
            method

            :returns:
            ----------
            - method_output (OrderedDict) : Ordered dictionary containing method output"""

        # Check input is in mapping and place method N output in instrument_dict to return
        try:
            method_output = self.create_method_mappings()[method_name](**method_args)
        except KeyError:
            logging.warning("Invalid Input - method '%s' does not exist try -help "
                            "to look at existing methods and arguments", method_name)
            method_output = None

        except TypeError:
            logging.warning("Invalid Input invalid addiitonal arguments entered "
                            "for method: '%s'", method_name)
            method_output = None
        return method_output

    @staticmethod
    def get_instrument_models():
        """ Returns a list of all currently active instruments
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :returns:
            ----------
            - instrument_list (list): list of instrument row proxy objects from Autoreduction
            database """

        instrument_list = query_argument_constructor.get_list_of_instruments()
        return instrument_list

    def run_every_instrument(self, instrument_dict, method_name, method_arguments=None):
        """ Returns all existing instruments in a dictionary for a given method as:
            {instrument_name : [[method output row 1]],[[method output row 2] etc] ...}
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - instrument_dict (dictionary):
            - method_name (string): method name to be called
            - method_arguments (NONE/dictionary): dictionary of argument keys and arguments or left
            as None


            :returns:
            ----------
            instrument_dict (dictionary): dictionary with instruments as keys and values as method
            output"""

        for instrument in self.get_instrument_models():
            try:
                method_arguments['instrument_id'] = int(instrument.id)
                logging.info("Querying for instrument: %s", method_arguments)
                instrument_dict[instrument.id] = \
                    self.create_method_mappings()[method_name](**method_arguments)
            except KeyError:
                logging.warning("Invalid Input - method '%s' does not exist try -help "
                                "to look at existing methods and arguments", method_name)
        return instrument_dict

    def user_instrument_list_validate(self, instrument_input):
        """ Compares list of instruments from user input with instruments in db.
            :return tuple of valid instruments in user input
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - instrument_input (list) list of strings of valid instrument names

            :returns:
            ----------
            valid_instrument_list (list) list of valid instrument row proxy objects"""

        valid_instruments_list = []
        list_of_instruments_from_db = self.get_instrument_models()

        for instrument_from_db in list_of_instruments_from_db:

            for instrument_from_user in instrument_input:
                if instrument_from_db.name == instrument_from_user:
                    valid_instruments_list.append(instrument_from_db)
        return valid_instruments_list

    def get_query_for_instruments(self, method_name, instrument_input=None,
                                  additional_method_arguments=None):
        """ Check method to gather specified statistics is valid
            Check list of instruments are valid to gather statistics for (exception for "all")
            Check validity of optional additional method arguments
            return all or specified instruments in dictionary and gathered statistics for a given
            method
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - method_name (string): The name of the method to run <"execution_times">
            - instrument_input (list): List of instruments formatted as strings <["MARI", "WISH"]>
            - additional_method_arguments (dictionary): Dictionary of additional arguments to pass
            specified method <{'status': 4,
                               'start_date': '2019-12-12',
                               'end_date': '2019-12-14'}>

            :returns:
            ----------
            - instrument_dict (dictionary): Dictionary of statistics from specified method for each
            specified instrument
            <{instrument_N :[[method output row 1], [...]],
                            [[method output row 2], [...]],
            instrument_N+1 : [[...]. ...], [], ...}>"""

        instrument_dict = {}

        # To allow for keys to still be added to dictionary such as the instrument_id
        if not additional_method_arguments:
            additional_method_arguments = {}

        # If input is None, run all instruments by default
        if not isinstance(instrument_input, list):
            logging.error("Value is not iterable, the first argument must be of type list")
            return None

        for instrument in instrument_input:
            # Run all instruments if user input specified "all"
            if instrument == 'all':
                return self.run_every_instrument(instrument_dict,
                                                 method_name,
                                                 additional_method_arguments)

            valid_instruments = self.user_instrument_list_validate(instrument_input)
            for instruments in valid_instruments:
                additional_method_arguments['instrument_id'] = instruments.id
                instrument_dict[instruments.name] = self.method_call(
                    method_name=method_name,
                    method_args=additional_method_arguments)

        return instrument_dict
