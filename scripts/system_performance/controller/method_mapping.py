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
from scripts.system_performance.models.query_argument_constructor import QueryConstructor


class MethodSelectorConfigurator(object):
    """Class containing logic to call N methods specified by user for N instruments + any additional
     method arguments specified"""
    @staticmethod
    def create_method_mappings():
        """A dictionary to map input, user specified methods to return equivalent method to be called
        TODO: Create execution_time_average and run_frequency_average methods"""

        return {'missing_run_numbers_report': QueryHandler().missing_run_numbers_report,
                'execution_times': QueryHandler().execution_times,
                # 'execution_time_average': self.execution_time_average, TODO create method
                'run_frequency': QueryHandler().run_frequency,
                # 'run_frequency_average': self.run_frequency_average _ TODO create method
               }

    def method_call(self, method_name, method_args):
        """Calls user specified method and returns statistics for a given instrument"""
        # Check input is in mapping and place method N output in instrument_dict to return
        try:
            method_output = self.create_method_mappings()[method_name](**method_args)
        except KeyError:
            logging.warn("Invalid Input - method '%s' does not exist try -help "
                          "to look at existing methods and arguments", method_name)
            method_output = None

        except TypeError:
            logging.warn("Invalid Input invalid addiitonal arguments entered "
                         "for method: '%s'", method_name)
            method_output = None
        return method_output

    @staticmethod
    def get_instrument_models():
        """Returns a list of all currently active instruments"""
        instrument_list = QueryConstructor().get_list_of_instruments()
        return instrument_list

    def run_every_instrument(self, instrument_dict, method_name, method_arguments=None):
        """Returns all existing instruments in a dictionary for a given method as:
        {instrument_name : [[method output row 1]],[[method output row 2] etc] ...}"""

        print('instrument dict')

        for instrument in self.get_instrument_models():
            try:
                # if method_name in self.create_method_mappings():
                method_arguments['instrument_id'] = int(instrument.id)
                logging.info("Querying for instrument: {}".format(method_arguments))
                instrument_dict[instrument[1]] = self.create_method_mappings()[method_name](**method_arguments)
            except KeyError:
                logging.warn("Invalid Input - method '%s' does not exist try -help "
                                 "to look at existing methods and arguments", method_name)
            print('Instrument dict')
            print(instrument_dict)
        return instrument_dict

    def get_query_for_instruments(self, method_name, instrument_input=None, additional_method_arguments=None):
        """Checks that the instrument_from_db's in method input exist and then calls
        and returns methods specified as input for each instrument_from_db placing in
        a dictionary as a nested list for each instrument_from_db as:
         {instrument_name : [[method output row 1]],[[method output row 2] etc.] ...}

        Run methods for each instrument_from_db name
        :param instrument_input: [(str), (str), ...] - Represents the instruments to be used in queries
        :param method_name: (str) -  The name of the methods to run
        :param additional_method_arguments - method arguments specified by user
        :return: A dictionary of instrument_from_db names (key) and list of method output (value)
         """

        instrument_dict = {}

        # To allow for keys to still be added to dictionary such as the instrument_id
        if not additional_method_arguments:
            additional_method_arguments = {}

        # If input is None, run all instruments by default
        if not isinstance(instrument_input, list):
            logging.error("Value is not iterable, the first argument must be of type list")
            return None

        list_of_instruments_from_db = self.get_instrument_models()

        for instrument_from_db in list_of_instruments_from_db:
            # Add instrument_from_db id to dictionary of method arguments
            additional_method_arguments['instrument_id'] = instrument_from_db[0]

            # for instrument_from_db in method input
            for instrument_from_user in instrument_input:
                # Run all instruments if user input specified "all"
                if instrument_from_user == 'all':
                    return self.run_every_instrument(instrument_dict,
                                                     method_name,
                                                     additional_method_arguments)

                elif instrument_from_db[1] == instrument_from_user:
                    instrument_dict[instrument_from_db[1]] = self.method_call(
                        method_name=method_name,
                        method_args=additional_method_arguments)
                else:
                    logging.info('The instrument_from_db: {} has not been found in '
                                 'the autoreduction database'.format(instrument_from_user))

        return instrument_dict


# ALL CODE BELOW IS FOR MANUAL TESTING ONLY AND SHOULD BE REMOVED ON FULL INTEGRATION
# -------------------------------------------------------------------------------------------------------------------- #

#
def cust_query_return(test_message, dictionary_out):
    """For use with manual testing only - REMOVE AFTER"""
    print("\n {}".format(test_message))
    print(dictionary_out)
    # for item in dictionary_out:
    #     print(item, dictionary_out[item])

#
# cust_query_return(test_message='Minimal Arguments - Select Instruments:',
#                   dictionary_out=MethodSelectorConfigurator().get_query_for_instruments(instrument_input=['MARI', 'MAPS'],
#                                                                           method_name='missing_run_numbers_report',
#                                                                           additional_method_arguments={
#                                                                               'start_date':'2019-12-12',
#                                                                               'end_date': '2019-12-13',}))


# # # Missing run numbers
# cust_query_return(test_message='missing_run_numbers_report - Select Instruments:',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['MARI', 'MAPS', 'WISH'],
#                                                                           method_name='missing_run_numbers_report',
#                                                                           additional_method_arguments={
#                                                                               'start_date':'2019-12-12',
#                                                                               'end_date': '2019-12-14'}))
# cust_query_return(test_message='missing_run_numbers_report - All Instruments:',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['all'],
#                                                                           method_name='missing_run_numbers_report',
#                                                                           additional_method_arguments={
#                                                                               'start_date': '2019-12-12',
#                                                                               'end_date': '2019-12-14'}))
#
# # Execution time
cust_query_return(test_message='execution_times - Select Instruments',
                  dictionary_out=MethodSelectorConfigurator().get_query_for_instruments(instrument_input=['MARI'],
                                                                          method_name='execution_times',
                                                                          additional_method_arguments={
                                                                              'start_date': '2019-12-12',
                                                                              'end_invalid': '2019-12-14'}))
# cust_query_return(test_message='execution_times - All Instruments:',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['all'],
#                                                                           method_name='execution_times',
#                                                                           additional_method_arguments={
#                                                                               'start_date': '2019-12-12',
#                                                                               'end_date': '2019-12-14'}))
#
# # Run frequency
# additional_args = {'status': 4, 'start_date': '2019-12-19', 'end_date': '2019-12-19'}
# cust_query_return(test_message='run_frequency - Select Instruments',
#                   dictionary_out=MethodSelectorConfigurator().get_query_for_instruments(instrument_input=['MARI', 'MAPS', 'WISH'],
#                                                                           method_name='run_frequency',
#                                                                           additional_method_arguments=additional_args))

# cust_query_return(test_message='run_frequency - Select Instruments',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['all'],
#                                                                           method_name='run_frequency',
#                                                                           additional_method_arguments=additional_args))
