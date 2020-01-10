# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Contains pre-logic data manipulation for more complex system performance MySQL queries.
"""

# Dependencies
from __future__ import print_function
import datetime
import time
import logging
import reduction_run_queries

from scripts.system_performance.query_constructor import QueryConstructor


class QueryHandler:
    """The query handler class returns a dictionary containing nested lists for each instrument and
     each query called in the user handler script"""

    def __init__(self):
        pass

    def create_method_mappings(self):
        """A dictionary to map input, user specified methods to return equivalent method to be called
        TODO: Create execution_time_average and run_frequency_average methods"""

        return {'missing_run_numbers_report': self.missing_run_numbers_report,
                'execution_times': self.execution_times,
                # 'execution_time_average': self.execution_time_average,
                'run_frequency': self.run_frequency,
                # 'run_frequency_average': self.run_frequency_average
               }

    @staticmethod
    def get_instrument_models():
        """Returns a list of all currently active instruments"""
        instrument_list = reduction_run_queries.DatabaseMonitorChecks().instruments_list()
        return instrument_list

    def run_every_instruments(self, instrument_dict, method_name, method_arguments=None):
        """Returns all existing instruments in a dictionary for a given method as:
        {instrument_name : [[method output row 1]],[[method output row 2] etc] ...}"""
        for instrument in self.get_instrument_models():
            try:
                if method_name in self.create_method_mappings():
                    method_arguments['instrument_id'] = int(instrument.id)
                    logging.info("Querying for instrument: {}".format(method_arguments))
                    print("Querying instrument: {}".format(instrument[1]))
                    instrument_dict[instrument[1]] = self.create_method_mappings()[method_name](**method_arguments)
            except KeyError:
                raise ValueError('Invalid Input - method {} does not exist'.format(method_name))
        return instrument_dict

    def get_query_for_instruments(self, method_name, instrument_input=None, additional_method_arguments=None):
        """Checks that the instrument's in method input exist and then calls
        and returns the method used as input for each instrument placing in
        a dictionary as a nested list for each instrument as:
         {instrument_name : [[method output row 1]],[[method output row 2] etc.] ...}

        Run methods for each instrument name
        :param instrument_input: [(str), (str), ...] - Represents the instruments to be used in queries
        :param method_name: (str) -  The name of the methods to run
        :param additional_method_arguments - method arguments specified by user
        :return: A dictionary of instrument names (key) and list of method output (value)
         """

        instrument_dict = {}

        # To allow for keys to still be added to dictionary such as the instrument_id
        if not additional_method_arguments:
            additional_method_arguments = {}

        for instrument in self.get_instrument_models():
            # Check for additional arguments and place in list with instrument id to pass as argument in method
            if not additional_method_arguments:
                additional_method_arguments['instrument_id'] = instrument[0]
            else:
                # Adds minimum arguments needed for method call to dictionary
                additional_method_arguments['instrument_id'] = instrument[0]

            # If input is None, run all instruments by default
            if not isinstance(instrument_input, list):
                logging.error("Value is not iterable, the first argument must be of type list")
                return None
            for instrument_element in instrument_input:
                if instrument[1] == instrument_element:
                    # Check input is in mapping and place method N output in instrument_dict to return
                    try:
                        if method_name in self.create_method_mappings():
                            instrument_dict[instrument[1]] = \
                                self.create_method_mappings()[method_name](**additional_method_arguments)
                    except KeyError:
                        raise ValueError('Invalid Input - method {} does not exist use type -help '
                                         'to look at existing methods and arguments'.format(method_name))
                # Run all instruments if user input specified "all"
                elif instrument_element == 'all':
                    return self.run_every_instruments(instrument_dict, method_name, additional_method_arguments)
                else:
                    logging.info('The instrument: {} has not been found in the autoreduction'
                                 ' database'.format(instrument_element))
        return instrument_dict

    @staticmethod
    def missing_run_numbers_report(instrument_id, start_date, end_date):
        """Retrieves missing run numbers from reduction to be analysed
        :returns [count of run run number between two dates/time,
                 the count of missing run numbers,
                 [nested list of missing run numbers id's]]"""

        def _find_missing(lst):
            """Find all missing numbers in a given list"""
            return [x for x in range(lst[0], lst[-1] + 1) if x not in lst]

        returned_query = QueryConstructor().missing_run_numbers_constructor(
            instrument_id=instrument_id,
            start_date=start_date,
            end_date=end_date)

        # Sort returned query run numbers into ascending order
        returned_query.sort()
        sorted_run_numbers = sorted(returned_query)
        missing_run_numbers = _find_missing(sorted_run_numbers)

        # return list containing count of runs vs count of missing runs
        return [len(sorted_run_numbers), len(missing_run_numbers), missing_run_numbers]

    @staticmethod
    def execution_times(instrument_id, start_date, end_date):
        """returns execution times for each instrument specified in method argument in a dictionary."""
        def _convert_seconds_to_time(time_in_seconds):
            """Converts seconds back into time format for output"""
            return str(datetime.timedelta(seconds=time_in_seconds))

        def _convert_time_to_seconds(time_format):
            """Converts time into seconds for calculating difference"""
            reformat_time = time.strptime(time_format, '%H:%M:%S')
            return datetime.timedelta(hours=reformat_time.tm_hour,
                                      minutes=reformat_time.tm_min,
                                      seconds=reformat_time.tm_sec).total_seconds()

        def _execution_times_in_seconds_mapping(start_end_times):
            """:returns a nested list of start and end times in seconds"""
            time_duration_list = []
            grouped_start_end_times = []

            for sublist in start_end_times:
                start_end = [sublist[2], sublist[3]]
                # Converting start and end times into seconds
                for time_returned in start_end:
                    time_duration_list.append(int(_convert_time_to_seconds(time_returned)))
                    if len(time_duration_list) == 2:
                        isolated_start_end_times = [time_duration_list[0], time_duration_list[1]]
                        grouped_start_end_times.append(isolated_start_end_times)
                        time_duration_list = []
            return grouped_start_end_times

        def _list_zip(execution_list, list_of_times):
            """Appending execution times to the ends of each start end sublist."""
            for execution_times in range(len(execution_list)):
                if execution_list[execution_times] is not None:
                    list_of_times[execution_times].append(execution_list[execution_times])
            return list_of_times

        def _calc_execution_times(list_of_times):
            """  Calculates execution times as appends to returned query list
            :returns list_of_times & execution times as [[id, run_number, start_time, end_time, execution_time]..]"""
            time_in_seconds_list = []

            # Calculate execution times and append to new list
            for start_end_sublist in _execution_times_in_seconds_mapping(list_of_times):
                time_in_seconds_list.append(start_end_sublist[1] - start_end_sublist[0])

            # Convert execution times from seconds to datetime format
            execution_list = []
            for times in time_in_seconds_list:
                execution_list.append(_convert_seconds_to_time(times))
            return _list_zip(execution_list, list_of_times)

        def _query_argument_specify(start_date, end_date):
            """Specifies arguments for query and returns formatted data from Autoreduce database"""

            set_query_arguments = QueryConstructor.query_argument_specify(
                instrument_id=instrument_id,
                start_date=start_date,
                end_date=end_date)

            return _calc_execution_times(set_query_arguments)

        return _query_argument_specify(start_date=start_date, end_date=end_date)

    # pylint: disable=line-too-long
    @staticmethod
    def run_frequency(instrument_id, status, retry=None, end_date=None, start_date=None, time_interval=None):
        # pylint: enable=line-too-long

        """Return run frequencies for N instruments of type: successful run, failed run, or retry run.
        Method output follows the format: Dict {instrument_N : [rpd, tr, rpw, rpw, rpm]}
        :param instrument_id Instrument by id 1=GEM; 2=Wish etc. - Check documentation for reference or use help method
        :param status Completion status e.g Error = 1; Queued = 2' Processing = 3; Completed = 4; Skipped = 5
        :param retry Takes input as True or left as None to obtain the count of retry runs
        :param end_date The most recent date you wish to get the count of dates up to - by default the value is now()
        :param start_date The Date you wish to count from up to the end date/ - by default this is set to None
        :param time_interval Interval of time as int to specify number of a time scale (1 DAY, 2 DAY etc) defaults to 1
        :param time_scale Time scale of choice such as DAY, WEEK, MONTH, YEAR. - by default this value will be set to 1
        :param sub_method_preference Allows all previous arguments other than instrument_id and status to be left empty
        to run a predefined argument such as runs in the last 24 hours, per day, per week, per month

        :return list of sub method values [runs_per_day(), runs_today(), runs_per_week(), runs_per_month()]

        """

        if start_date is None:
            start_date = datetime.date.today() - datetime.timedelta(days=2)

        if time_interval is None:
            time_interval = 1

        if end_date is None:
            end_date = datetime.date.today()

        def _runs_per_day():
            """Returns count of runs in the last 24 hours for current date of specified date """
            # Defaults for time, only exception is changing end_date to look in the past

            return QueryConstructor().runs_per_day(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date
            )

        def _runs_today():
            """Returns all runs equal to current date."""

            return QueryConstructor().runs_today(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date,
                start_date=start_date)

        def _runs_per_week():
            """Returns count of runs that have taken place over the course of the week if the day of week is Friday."""
            # If today is last day of week (Friday in this case) run, otherwise don't unless user specified to
            return QueryConstructor().runs_per_week(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date,
                time_interval=time_interval)

        def _runs_per_month():
            """Returns count of runs that occurred over the last month if day is equal to end of month"""
            # If today is last day of month, run, otherwise don't unless user specified to

            return QueryConstructor().runs_per_month(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date,
                time_interval=time_interval)

        def _query_execute():
            """Converts sub_method outputs into a dictionary where key is instrument
            - If not friday, runs_per_week will return none
            - If not last day of the month, runs_per_month will return none
            """

            def list_lengths(nested_list_of_runs):
                """ Returning run count of runs for each frequency range"""
                run_frequency_list_counts = []
                for frequency_interval in nested_list_of_runs:
                    if frequency_interval:
                        run_frequency_list_counts.append(len(frequency_interval))
                    else:
                        run_frequency_list_counts.append(frequency_interval)
                return run_frequency_list_counts

            # Nested list containing run numbers for each frequency range
            run_frequency_list = [_runs_per_day(), _runs_today(), _runs_per_week(), _runs_per_month()]

            # Mapping both lists together to return in the form [[()), (), ... runs_per_day frequency], ... ]
            frequencies = list_lengths(run_frequency_list)
            for frequency_count in range(len(frequencies)):
                if frequencies[frequency_count] is not None:
                    run_frequency_list[frequency_count].append(frequencies[frequency_count])

            return run_frequency_list
        return _query_execute()

# ALL CODE BELOW IS FOR MANUAL TESTING ONLY AND SHOULD BE REMOVED ON FULL INTEGRATION
# -------------------------------------------------------------------------------------------------------------------- #

# def cust_query_return(test_message, dictionary_out):
#     """For use with manual testing only - REMOVE AFTER"""
#     print("\n {}".format(test_message))
#     for item in dictionary_out:
#         print(item, dictionary_out[item])
# #
# # # Missing run numbers
# cust_query_return(test_message='missing_run_numbers_report - Select Instruments:',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['MARI', 'MAPS', 'WISH'],
#                                                                           method_name='missing_run_numbers_report',
#                                                                           additional_method_arguments={
#                                                                               'start_date':'2019-12-12',
#                                                                               'end_date': '2019-12-14'}))
#
# cust_query_return(test_message='missing_run_numbers_report - All Instruments:',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['all'],
#                                                                           method_name='missing_run_numbers_report',
#                                                                           additional_method_arguments={
#                                                                               'start_date': '2019-12-12',
#                                                                               'end_date': '2019-12-14'}))
#
# # Execution time
# cust_query_return(test_message='execution_times - Select Instruments',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['MARI', 'MAPS', 'WISH'],
#                                                                           method_name='execution_times',
#                                                                           additional_method_arguments={
#                                                                               'start_date': '2019-12-12',
#                                                                               'end_date': '2019-12-14'}))
# cust_query_return(test_message='execution_times - All Instruments:',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['all'],
#                                                                           method_name='execution_times',
#                                                                           additional_method_arguments={
#                                                                               'start_date': '2019-12-12',
#                                                                               'end_date': '2019-12-14'}))
#
# # # Run frequency
# additional_args = {'status': 4, 'start_date': '2019-12-19', 'end_date': '2019-12-19'}
# cust_query_return(test_message='run_frequency - Select Instruments',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['MARI', 'MAPS', 'WISH'],
#                                                                           method_name='run_frequency',
#                                                                           additional_method_arguments=additional_args))
#
# cust_query_return(test_message='run_frequency - Select Instruments',
#                   dictionary_out=QueryHandler().get_query_for_instruments(instrument_input=['all'],
#                                                                           method_name='run_frequency',
#                                                                           additional_method_arguments=additional_args))

# TODO: Create this method
# To allow for the creation of a custom query between any dates/time period using get_status_over_time method
# This method will be for users and therefore will not be executed in the production script.
# pass
