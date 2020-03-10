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


class QueryHandler:  # pylint disable=too-few-public-methods
    """The query handler class returns a dictionary containing nested lists for each instrument and
     each query called"""

    def __init__(self):
        self.execution_times_dict = OrderedDict()
        self.execution_times_dict['id'] = []
        self.execution_times_dict['run_number'] = []
        self.execution_times_dict['start_time'] = []
        self.execution_times_dict['end_time'] = []
        self.execution_times_dict['execution_time'] = []

    @staticmethod
    def convert_seconds_to_time(time_in_seconds):
        """Converts seconds back into time format for output
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - time_in_seconds (int): Time in seconds as integer

            :returns:
            ----------
            - time_in_seconds (datetime.time): convert integer to time format"""

        return str(datetime.timedelta(seconds=time_in_seconds))

    @staticmethod
    def convert_time_to_seconds(time_format):
        """Converts time into seconds for calculating difference
             =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            time_format (datetime.time): Time in seconds as integer

            :returns:
            ----------
            - time_format (int): convert time to integer format"""

        reformat_time = time.strptime(time_format, '%H:%M:%S')
        return datetime.timedelta(hours=reformat_time.tm_hour,
                                  minutes=reformat_time.tm_min,
                                  seconds=reformat_time.tm_sec).total_seconds()

    @staticmethod
    def find_missing_numbers_in_list(list_of_rb_numbers):
        """Find all missing rb numbers in a given list
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - list_of_rb_numbers (list): List of rb numbers

            :returns:
            ----------
            - list_of_rb_numbers (list): List of missing rb numbers

            :raises
            ----------
            - IndexError: Index not found in list_of_rb_numbers"""

        try:
            return [rb_number for rb_number in range(list_of_rb_numbers[0],
                                                     list_of_rb_numbers[-1] + 1)
                    if rb_number not in list_of_rb_numbers]
        except IndexError:
            logging.warning("Index Error while trying to look for missing \
            run number in list_of_rb_numbers %s", list_of_rb_numbers)
            return None

    @staticmethod
    def list_zip(execution_list, list_of_times):
        """Appending execution times to the ends of each start-end sublist.
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - execution_list (list): List of execution times
            - list_of_times (list) List of run start and end times

            :returns:
            ----------
            - list_of_times (list): Zipped list of times and execution times"""

        for execution_times in range(len(execution_list)): #pylint: disable=consider-using-enumerate
            if execution_list[execution_times] is not None:
                list_of_times[execution_times].append(execution_list[execution_times])
        print("list zip")
        print(list_of_times)
        return list_of_times

    def list_extraction_and_isolation(self, start_end_times, start_time_index, end_time_index):
        """ Extracts execution times from each sublist into a separate nested
            list converted to seconds
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - start_end_times (list): List od lists containing start, end and ex
            - start_time_index (int) Index of where start time is located inn sub-lists
            - end_time_index (int): Index of where end time is located in sub-lists

            :returns
            ----------
            - grouped_start_end_times (list): nested list of start and end times in seconds"""

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
        """ convert nested lists into dictionary to allow for searching by key
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - list_of_list (list): list of start, end and execution times
            - execution_dict (Ordered dictionary): unpopulated Dictionary containing keys for: id,
            run_number,
            - start_time, end_time and execution time

            :returns
            ----------
            - execution_dict (dictionary): Populated dictionary"""

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
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - instrument_id (int): instrument ID as seen in Autoreduction Database
            - start_date (string): string containing date formatted as yyyy-mm-dd
            - end_date (string): string containing date formatted as yyyy-mm-dd

            :returns
            ----------
            - dictionary: Dictionary of nested list to to be referenced later to an instrument
                    [count of run run number between two dates/time,
                     the count of missing run numbers,
                     [nested list of missing run numbers id's]]"""

        # Sort returned query run numbers into ascending order
        sorted_run_numbers = sorted(query_argument_constructor.runs_in_date_range(
            instrument_id=instrument_id,
            start_date=start_date,
            end_date=end_date))

        missing_run_numbers = self.find_missing_numbers_in_list(sorted_run_numbers)
        if sorted_run_numbers:
            count_of_runs = len(sorted_run_numbers)
            missing_runs_count = len(missing_run_numbers)
        else:
            count_of_runs = None
            missing_runs_count = None

        # return list containing count of runs vs count of missing runs
        return {'Count_of_runs': count_of_runs,
                'Missing_runs_count': missing_runs_count,
                'Missing_runs': missing_run_numbers}

    def execution_times(self, instrument_id, start_date, end_date):
        """returns execution times for each instrument specified in method argument
            in a dictionary.
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            = instrument_id (int): instrument ID as seen in Autoreduction Database
            = start_date (string): string containing date formatted as yyyy-mm-dd
            - end_date (string): string containing date formatted as yyyy-mm-dd

            :returns
            ----------
            - dictionary: dictionary of execution times for a given instrument"""

        def _query_argument_specify(start_date, end_date):
            """Specifies arguments for query and returns formatted data from Autoreduce database
                =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

                :parameter
                ----------
                - start_date (string): string containing date formatted as yyyy-mm-dd
                - end_date (string): string containing date formatted as yyyy-mm-dd

                :returns
                ----------
                - list: nested list of queried data from database"""

            return query_argument_constructor.start_and_end_times_by_instrument(
                instrument_id=instrument_id,
                start_date=start_date,
                end_date=end_date)

        time_in_seconds_list = []
        execution_times_dict = self.execution_times_dict  # Creating ordered dictionary to append to

        # Calculate execution times and append to new list
        list_of_times = _query_argument_specify(start_date, end_date)

        # Isolate start and end times and place in separate list of lists
        for start_end_sublist in self.list_extraction_and_isolation(list_of_times, 2, 3):
            # Calc exe times from isolated start end times, placing in new list in datetime format
            time_in_seconds_list.append(self.convert_seconds_to_time(start_end_sublist[1] - start_end_sublist[0]))  # pylint: disable=line-too-long

        # Construction of output for a given instrument and return in dictionary
        return self.nested_lists_to_dict(self.list_zip(time_in_seconds_list,
                                                       list_of_times),
                                         execution_times_dict)

    @staticmethod
    def run_frequency(instrument_id, status, retry=None, end_date=None, start_date=None, time_interval=None):  # pylint: disable=too-many-arguments, line-too-long

        """ Return run frequencies for N instruments of type: successful run, failed run, or retry
            run.
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - instrument_id (int): Instrument by id 1=GEM; 2=Wish etc. - Check documentation for
            reference or use help method
            - status (int): Completion status e.g Error = 1; Queued = 2' Processing = 3;
            Completed = 4;
            Skipped = 5
            - retry (bool): Takes input as True or left as None to apply a filter by whether or not
            a run has been retried or not
            - end_date (string): Most recent date you wish to get the count of dates up to - by
            default
            - start_date (string): Date you wish to from to the end date/ - by default this is None
            - time_interval (int): Interval of time as int to specify number of a time scale (1 DAY,
             2 DAY etc) default value is 1


            :returns
            ----------
            - run_frequency_list (list): list of sub method values [runs_per_day(), runs_today(),
            runs_per_week(), runs_per_month()]"""

        # Setting default values if none
        if start_date is None:
            start_date = datetime.date.today() - datetime.timedelta(days=2)

        if time_interval is None:
            time_interval = 1

        if end_date is None:
            end_date = datetime.date.today()

        if retry is None:
            retry = ''

        def _runs_per_day():
            """ Returns count of runs in the last 24 hours for current date of specified date
                =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

                :returns
                ----------
                - list: list of runs in from the last 24 hrs """

            # Defaults for time, only exception is changing end_date to look in the past
            return query_argument_constructor.runs_per_day(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date)

        def _runs_today():
            """ Returns all runs equal to current date.
                =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

                :returns
                ----------
                - list: list of runs which took place today """

            return query_argument_constructor.runs_today(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date,
                start_date=start_date)

        def _runs_per_week():
            """ Returns count of runs that have taken place over the course of the week if the day
                of week is Friday.
                =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

                :returns
                ----------
                - list or runs which took place over the last week """

            # If today is last day of week (Friday in this case) run, otherwise don't unless user
            # specified to
            return query_argument_constructor.runs_per_week(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date,
                time_interval=time_interval)

        def _runs_per_month():
            """ Returns count of runs that occurred over last month if day is end of month
                =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
                :returns
                ----------
                - list of runs which took place over the last month"""

            # If today is last day of month, run, otherwise don't unless user specified to
            return query_argument_constructor.runs_per_month(
                instrument_id=instrument_id,
                status=status,
                retry=retry,
                end_date=end_date,
                time_interval=time_interval)

        def _query_execute():
            """ Converts sub_method outputs into a dictionary where key is instrument
                - If not friday, runs_per_week will return none
                - If not last day of the month, runs_per_month will return none
                =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

                :returns
                ----------
                - list: Mapped list of runs per... and count of runs
                """

            def list_lengths(nested_list_of_runs):
                """ Returning run count of runs for each frequency range
                    =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
                    :parameter
                    ----------
                    - nested_list_of_runs (list): nested list containing [[rpd], [rt], [rpw], [rpm]]
                    :returns
                    ----------
                    - list contains list of counts of sub-lists """
                run_frequency_list_counts = []
                for frequency_interval in nested_list_of_runs:
                    if frequency_interval:
                        run_frequency_list_counts.append(len(frequency_interval))
                    else:
                        run_frequency_list_counts.append(frequency_interval)
                return run_frequency_list_counts

            # Nested list containing run numbers for each frequency range
            run_frequency_list = [_runs_per_day(), _runs_today(), _runs_per_week(), _runs_per_month()]  # pylint: disable=line-too-long

            # Mapping both lists together to return in the form [[()), (), runs_per_day frequency],]
            frequencies = list_lengths(run_frequency_list) # pylint: disable=consider-using-enumerate
            for frequency_count in range(len(frequencies)):  # pylint: disable=consider-using-enumerate
                if frequencies[frequency_count] is not None:
                    run_frequency_list[frequency_count].append(frequencies[frequency_count])

            return run_frequency_list
        return _query_execute()
