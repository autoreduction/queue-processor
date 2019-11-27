# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Contains pre-logic data manipulation for more complex system performance MySQL queries.
"""

# Dependencies
from datetime import date
from calendar import monthrange
import datetime
import time

import logging

from scripts.system_performance.beam_status_webscraper import DatabaseMonitorChecks
from scripts.system_performance.date_in_cycle import DateInCycle


class QueryHandler:
    """The query handler class returns one one or a list of query results to the user handler script"""

    def __init__(self):
        pass

    def create_method_mappings(self):
        """A dictionary to map input, user specified methods to return equivalent method to be called
        TODO: Create execution_time_average and run_frequency_average methods"""

        return {'missing_run_numbers_report': self.missing_run_numbers_report,
                'execution_time': self.execution_time,
                # 'execution_time_average': self.execution_time_average,
                'run_frequency': self.run_frequency,
                # 'run_frequency_average': self.run_frequency_average
                }

    @staticmethod
    def get_instrument_models():
        """Returns a list of all currently active instruments"""
        instrument_list = DatabaseMonitorChecks.list_instruments()
        return instrument_list

    def run_every_instruments(self, instrument_dict, method_name, method_arguments=None):
        """Returns all existing instruments in a dictionary for a given method as:
        {instrument_name : [[method output row 1]],[[method output row 2] etc] ...}"""
        for instrument in self.get_instrument_models():
            try:
                if method_name in self.create_method_mappings():
                    instrument_dict[instrument[1]] = self.create_method_mappings()[method_name](*method_arguments)
            except KeyError:
                raise ValueError('Invalid Input - method {} does not exist'.format(method_name))
        return instrument_dict

    def get_query_for_instruments(self, instrument_input, method_name, additional_method_arguments=None):
        """Checks that the instrument's in method input exist and then calls
        and returns the method used as input for each instrument placing in
        a dictionary as a nested list for each instrument as:
         {instrument_name : [[method output row 1]],[[method output row 2] etc.] ...}

        Run methods for each instrument name
        :param instrument_input: [(str), (str), ...] - Represents the instruments to be used in queries
        :param method_name: (str) -  The name of the methods to run
        :param additional_method_arguments - method arguments specified by user
        :return: A dictionary of instrument name (key) and list of method output (value)
         """

        instrument_dict = {}

        for instrument in self.get_instrument_models():
            # Check for additional arguments and place in list with instrument id to pass as argument in method
            if not additional_method_arguments:
                method_arguments = [instrument[0]]
            else:
                # convert arguments to list
                method_arguments = [instrument[0]] + additional_method_arguments

            # if input is None, run all instruments by default
            if not isinstance(instrument_input, list):
                logging.error("Value is not iterable, the first argument must be of type list")
                return None
            for instrument_element in instrument_input:
                if instrument[1] == instrument_element:
                    # Check input is in mapping and place method N output in instrument_dict to return
                    try:
                        if method_name in self.create_method_mappings():
                            instrument_dict[instrument[1]] = \
                                self.create_method_mappings()[method_name](*method_arguments)
                    except KeyError:
                        raise ValueError('Invalid Input - method {} does not exist use type -help '
                                         'to look at existing methods and arguments'.format(method_name))
                # Run all instruments if user input specified "all"
                elif instrument_element == 'all' or not instrument_element:
                    self.run_every_instruments(instrument_dict, method_name, method_arguments)
                else:
                    logging.info('The instrument: {} has not been found in the autoreduction'
                                 ' database'.format(instrument_element))
        return instrument_dict

    @staticmethod
    def missing_run_numbers_report(instrument_id):
        """Retrieves missing run numbers from reduction to be analysed"""

        # returned query format: [number_of_rows, max_rb_number, min_rb_number, [table_list]]
        returned_query = DatabaseMonitorChecks.missing_rb_report(instrument_id)
        # Make ordered list from min_rb to max_rb
        reference_list = [item for item in range(returned_query[2],
                                                 returned_query[1] + 1)]
        row_range = returned_query[1] - returned_query[2]

        # Shouldn't be possible to have a higher row range than there are rows
        if row_range > returned_query[0]:
            logging.ERROR(
                'bd_state_checks: Row range is larger than row count {} > {}'.format(row_range, returned_query[0]))
        # Missing Values are present invoking the need to query which run numbers are missing
        elif row_range < returned_query[0]:
            logging.warning(
                'bd_state_checks: Missing run numbers are present - row range is smaller than row count {} < {}'.format(
                    row_range, returned_query[0]))
            # Compare reference list to actual run numbers to find missing run numbers
            missing_reduction_numbers = list(set(reference_list) - set(returned_query[3]))
            return missing_reduction_numbers
        # Else all run numbers are present in asynchronous order
        else:
            logging.info('All run numbers are present in asynchronous order.')

    @staticmethod
    def convert_time_to_seconds(time_format):
        """Converts time into seconds for calculating difference"""
        reformat_time = time.strptime(time_format, '%H:%M:%S')
        return datetime.timedelta(hours=reformat_time.tm_hour,
                                  minutes=reformat_time.tm_min,
                                  seconds=reformat_time.tm_sec).total_seconds()

    @staticmethod
    def convert_seconds_to_time(time_in_seconds):
        """Converts seconds back into time format for output"""
        return str(datetime.timedelta(seconds=time_in_seconds))

    @staticmethod
    def execution_time(instrument=None):
        """
        Calculates the execution time taken for each run returning in time format

        :param instrument: Instrument name taken as input and convert to instrument id
                            - Data type is assumed to ba of type list if not None.
        :return Dictionary containing one or many instruments as keys containing nested lists of execution times
        """

        def _append_execution_times(start_end_times, execution):
            """ Append to the end of each nested list
                start_end_times now returns format:
                [[id, run_number, start_time, end_time, execution_time], [ ...], ... ] """

            start_end_execution = iter(execution)
            for nested_list in start_end_times:
                for element in nested_list:
                    if isinstance(element, list):
                        element.append(next(start_end_execution))
                    else:
                        nested_list.append(next(start_end_execution))
                        break
            return start_end_times

        def _calc_execution_times(list_of_times):
            """Calculate execution time and append to list"""
            for execution_list in list_of_times:
                # Convert time HH:MM:SS into seconds to calculate execution time then converts back to time HH:MM:SS
                time_duration_list = []
                start_end = [execution_list[2], execution_list[3]]
                for time_returned in start_end:
                    # Appends time in seconds to list
                    time_duration_list.append(int(DateInCycle.convert_time_to_seconds(time_returned)))
                # Calculate difference in time
                time_duration = time_duration_list[1] - time_duration_list[0]
                # Converts back to datetime
                execution = DateInCycle.convert_seconds_to_time(time_duration)
                # Appends execution time to the end of each sublist
                return _append_execution_times(list_of_times, execution)

        # new_start_end_times returned format: [[id, run_number, start_time, end_time], [ ...], ... ]
        new_start_end_times = DatabaseMonitorChecks.run_times(instrument)
        return _calc_execution_times(new_start_end_times)

    # pylint: disable=line-too-long
    @staticmethod
    def run_frequency(instrument_id, status, retry=None, end_date=None, start_date=None, time_interval=None, sub_method_preference=None):
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

        :return list of sub method values [_runs_per_day(), _runs_today(), _runs_per_week(), _runs_per_month()]

        TODO: Create means to use sub_method_preference input to choose only specified sub methods as to running all \
               methods by default unless set to None

        """

        if start_date is None:
            start_date = 'curdate()'

        if time_interval is None:
            time_interval = 1

        def _runs_per_day(**args):
            """"""
            # Defaults for time, only exception is changing end_date to look at one day in the past
            return DatabaseMonitorChecks.get_data_by_status_over_time(instrument_id,
                                                                      status,
                                                                      retry,
                                                                      end_date)

        def _runs_today(**args):
            """"""
            # start_date = curdate()
            return DatabaseMonitorChecks.get_data_by_status_over_time(instrument_id,
                                                                      status,
                                                                      retry,
                                                                      end_date,
                                                                      start_date)

        def _runs_per_week(**args):
            """"""
            # times_scale = week
            # if today is last day of week (sunday in this case) run, otherwise don't unless user specified to
            if date.today().weekday() == 7:
                return DatabaseMonitorChecks.get_data_by_status_over_time(instrument_id,
                                                                          status,
                                                                          retry,
                                                                          end_date,
                                                                          time_interval,
                                                                          time_scale='WEEK')
            else:
                return None

        def _runs_per_month(**args):
            """"""
            # time_scale = month
            # if today is last day of month run, otherwise don't, unless user specified to
            if date.today() == monthrange(date.today().year, date.today().month)[1]:
                return DatabaseMonitorChecks.get_data_by_status_over_time(instrument_id,
                                                                          status,
                                                                          retry,
                                                                          end_date,
                                                                          time_interval,
                                                                          time_scale='MONTH')
            else:
                return None

        def _query_execute(**args):
            """Converts sub_method outputs into a dictionary where key is instrument
            - If not friday, _runs_per_week will return none
            - If not last day of the month, _runs_per_month will return none
            """

            run_frequency_list = [_runs_per_day(), _runs_today(), _runs_per_week(), _runs_per_month()]
            return run_frequency_list
        return _query_execute()

    def custom_query(self):
        # TODO: Create this method
        # To allow for the creation of a custom query between any dates/time period using get_status_over_time method
        # This method will be for users and therefore will not be executed in the production script.
        pass
