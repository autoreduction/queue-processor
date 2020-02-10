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
from collections import OrderedDict

from scripts.system_performance.models import query_argument_constructor


class QueryHandler:
    """The query handler class returns a dictionary containing nested lists for each instrument and
     each query called in the user handler script"""

    def __init__(self):
        pass

    @staticmethod
    def convert_seconds_to_time(time_in_seconds):
        """Converts seconds back into time format for output"""
        return str(datetime.timedelta(seconds=time_in_seconds))

    @staticmethod
    def convert_time_to_seconds(time_format):
        """Converts time into seconds for calculating difference"""
        reformat_time = time.strptime(time_format, '%H:%M:%S')
        return datetime.timedelta(hours=reformat_time.tm_hour,
                                  minutes=reformat_time.tm_min,
                                  seconds=reformat_time.tm_sec).total_seconds()

    @staticmethod
    def find_missing_numbers_in_list(list_of_rb_numbers):
        """Find all missing numbers in a given list"""
        try:
            return [rb_number for rb_number in range(list_of_rb_numbers[0],
                                                     list_of_rb_numbers[-1] + 1)
                    if rb_number not in list_of_rb_numbers]
        except IndexError:
            logging.warn("Index Error while trying to look for missing \
            run number in list_of_rb_numbers %s",list_of_rb_numbers)
            return None


    @staticmethod
    def list_zip(execution_list, list_of_times):
        """Appending execution times to the ends of each start-end sublist."""
        for execution_times in range(len(execution_list)):
            if execution_list[execution_times] is not None:
                list_of_times[execution_times].append(execution_list[execution_times])
        return list_of_times

    def list_extraction_and_isolation(self, start_end_times, start_time_index, end_time_index):
        """ Extracts execution times from each sublist into a separate nested
        list converted to seconds
        :returns a nested list of start and end times in seconds"""
        grouped_start_end_times = []

        for sublist in start_end_times:
            start_end = [sublist[start_time_index], sublist[end_time_index]]

            time_duration_list = []
            # Converting start and end times into seconds
            for time_returned in start_end:
                time_duration_list.append(int(self.convert_time_to_seconds(time_returned)))

                # Placing pairs of start and end times inside sublist
                if len(time_duration_list) == 2:
                    grouped_start_end_times.append([time_duration_list[0], time_duration_list[1]])
        return grouped_start_end_times

    @staticmethod
    def nested_lists_to_dict(list_of_lists, execution_dict):
        execution_cols = list(execution_dict.keys())
        for execution_times_list in list_of_lists:
            col_index = 0
            while col_index < 5:
                try:
                    execution_dict[execution_cols[col_index]].append(
                        execution_times_list[col_index])
                except KeyError:
                    execution_dict[execution_cols[col_index]] = execution_times_list[col_index]
                col_index = col_index + 1
        return execution_dict

    def missing_run_numbers_report(self, instrument_id, start_date, end_date):
        """Retrieves missing run numbers from reduction to be analysed
        :returns [count of run run number between two dates/time,
                 the count of missing run numbers,
                 [nested list of missing run numbers id's]]"""

        # Sort returned query run numbers into ascending order
        sorted_run_numbers = sorted(query_argument_constructor.missing_run_numbers_constructor(
            instrument_id=instrument_id,
            start_date=start_date,
            end_date=end_date))

        print('sorted run numbers')
        print(sorted_run_numbers)

        missing_run_numbers = self.find_missing_numbers_in_list(sorted_run_numbers)

        # return list containing count of runs vs count of missing runs
        return {'Count_of_runs': len(sorted_run_numbers),
                'Missing_runs_count': len(missing_run_numbers),
                'Missing_runs': missing_run_numbers}

    def execution_times(self, instrument_id, start_date, end_date):
        """returns execution times for each instrument specified in method argument
        in a dictionary."""
        time_in_seconds_list = []
        execution_times_dict = OrderedDict()
        execution_times_dict['id'] = []
        execution_times_dict['run_number'] = []
        execution_times_dict['start_time'] = []
        execution_times_dict['end_time'] = []
        execution_times_dict['execution_time'] = []
        # {'id': [], 'run_number': [], 'start_time': [], 'end_time': [],
        #                         'execution_time': []}

        def _query_argument_specify(start_date, end_date):
            """Specifies arguments for query and returns formatted data from Autoreduce database"""

            return query_argument_constructor.start_and_end_times_by_instrument(
                instrument_id=instrument_id,
                start_date=start_date,
                end_date=end_date)

        # Calculate execution times and append to new list
        list_of_times = _query_argument_specify(start_date, end_date)

        # Isolate start and end times and place in separate list of lists
        for start_end_sublist in self.list_extraction_and_isolation(list_of_times, 2, 3):
            # Calc exe times from isolated start end times, placing in new list in datetime format
            time_in_seconds_list.append(self.convert_seconds_to_time(start_end_sublist[1] - start_end_sublist[0]))

        # Construction of output for a given instrument and return in dictionary
        return self.nested_lists_to_dict(self.list_zip(time_in_seconds_list,
                                                       list_of_times),
                                         execution_times_dict)

    @staticmethod
    def run_frequency(instrument_id, status, retry=None, end_date=None, start_date=None, time_interval=None):  # pylint: disable=line-too-long

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

        if retry is None:
            retry = ''

        def _runs_per_day():
            """Returns count of runs in the last 24 hours for current date of specified date """
            # Defaults for time, only exception is changing end_date to look in the past
            return query_argument_constructor.runs_per_day(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date
            )

        def _runs_today():
            """Returns all runs equal to current date."""
            print('today')
            return query_argument_constructor.runs_today(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date,
                start_date=start_date)

        def _runs_per_week():
            """Returns count of runs that have taken place over the course of the week if the day of week is Friday."""
            # If today is last day of week (Friday in this case) run, otherwise don't unless user specified to
            return query_argument_constructor.runs_per_week(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date,
                time_interval=time_interval)

        def _runs_per_month():
            """Returns count of runs that occurred over the last month if day is equal to end of month"""
            # If today is last day of month, run, otherwise don't unless user specified to

            return query_argument_constructor.runs_per_month(
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

# TODO: Create this method
# To allow for the creation of a custom query between any dates/time period using get_status_over_time method
# This method will be for users and therefore will not be executed in the production script.
# pass
