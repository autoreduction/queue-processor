# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Contains pre-logic data manipulation for more complex system performance MySQL queries.
"""

from datetime import date

# Database Client
import logging
# import os
# import sys
import datetime
import time

# sys.path.append(os.path.join(os.path.dirname(__file__), '../..', 'utils'))
from scripts.system_performance.beam_status_webscraper import Data_Clean, TableWebScraper
from scripts.system_performance.beam_status_webscraper import DatabaseMonitorChecks
from utils.clients.database_client import DatabaseClient

# Set url to scrape from, put inside pandas table and clean data frame ready for queries
url = 'https://www.isis.stfc.ac.uk/Pages/Beam-Status.aspx'
df = Data_Clean(TableWebScraper(url).create_table()).normalise()


# -///////////////////////////////////////// Query Pre Logic  /////////////////////////////////////////-#

class DateInCycle:

    def __init__(self, data_frame, start_col, end_col, current_date=None):
        self.data_frame = data_frame
        self.start_col = start_col
        self.end_col = end_col

        # By default use the current date, but allow custom date for a given instance of date_in_cycle
        if not self.current_date:
            self.current_date = date.today()
        else:
            self.current_date = current_date

    # Get cycle start and end date for a given row in start and end columns

    # Compare start and end date returned from above function.

    # (A) Check if current_date is in between start and end start < today < end

    # (B) Check if current date is between end date and start date  end > today < next rows start

    @staticmethod
    def cycle_dates(row):
        """Returns cycle start and end dates row from df"""
        dates = []
        dates.extend(row[0], row['Start'], row['End'])
        return dates

    def cycle_search(self, column, row_id):
        """Search for a specific row in cycle data frame"""
        target_row = []
        for col in column:

            target_row.append(self.data_frame.iloc[row_id][col])
        return target_row

    def in_cycle(self):
        """Check if current date is in or between a cycle"""
        point_in_cycle = None
        while not point_in_cycle:
            for row in self.data_frame:
                cycle = self.cycle_dates(row)
                point_in_cycle = self.date_in_cycle(cycle[0], cycle[1], cycle[2])
                return point_in_cycle

    def date_in_cycle(self, index, start, end):
        """Actions performed based on current date being inside a cycle or between cycles"""
        # Current date in cycle
        if start < self.current_date < end:
            # Want to look in current cycle
            run_performance_count = self.run_fail_count(start, end)

            in_cycle = None
            return in_cycle

        # checking if current date is between cycles (# "index+1" to look at next rows start date)
        if index < self.data_frame.tail(1).index.item():
            if self.current_date > end < self.cycle_search([self.start_col], index+1):
                # want to look at previous cycle
                dates = self.cycle_search([self.start_col, self.end_col],index+1)
                start, end = dates[0], dates[1]
                run_performance_count = self.run_fail_count(start, end)

                in_cycle = None
                return in_cycle
            # Edge case for current date not in a cycle or between cycles (covers maintenance days when added)
            else:
                in_cycle = None
                return in_cycle
        # Looking at last row in data frame. Current date can't be checked any further back in time
        else:
            in_cycle = None
            return in_cycle

    def create_method_mappings(self):
        """A dictionary to map on input, user specified methods to return to equivalent method to be called"""
        return {'missing_run_numbers_report': self.missing_run_numbers_report,
                'execution_time': self.execution_time,
                'execution_time_average': self.execution_time_average,
                'run_frequency': self.run_frequency,
                'run_frequency_average': self.run_frequency_average
                }

    @staticmethod
    def get_instrument_models():
        """Returns a list of all currently active instruments"""
        instrument_list = DatabaseMonitorChecks.list_instruments()
        return instrument_list

    def run_every_instruments(self, instrument_dict, method_name):
        """Returns all existing instruments in a dictionary for a given method as:
        {instrument_name : [[method output row 1]],[[method output row 2] etc] ...}"""
        for instrument in self.get_instrument_models():
            try:
                if method_name in self.create_method_mappings():
                    instrument_dict[instrument[1]] = self.create_method_mappings()[method_name](instrument[0])
            except KeyError:
                raise ValueError('Invalid Input - method {} does not exist'.format(method_name))
        return instrument_dict

    def get_query_for_instruments(self, instrument_input, method_name):
        """Checks that the instrument's in method input exist and then calls
        and returns the methods used as input for each instrument placing in
        a dictionary as a nested list for each instrument as:
         {instrument_name : [[method output row 1]],[[method output row 2] etc.] ...}

        Run methods for each instrument name
        :param instrument_input: [(str), (str), ...] - Represents the instruments to be used in queries
        :param method_name: (str) -  The name of the methods to run
        :return: A dictionary of instrument name (key) and list of method output (value)

         """
        instrument_dict = {}

        for instrument in self.get_instrument_models():
            # if input is None, run all instruments by default
            if not isinstance(instrument_input, list):
                logging.error("Value is not iterable, the first argument must be of type list")
                return None
            for instrument_element in instrument_input:
                if instrument[1] == instrument_element:
                    # check input is in mapping and place method output in instrument_dict
                    try:
                        if method_name in self.create_method_mappings():
                            instrument_dict[instrument[1]] = self.create_method_mappings()[method_name](instrument[0])
                    except KeyError:
                        raise ValueError('Invalid Input - method {} does not exist'.format(method_name))
                # Run all methods is user specifies "all"
                elif instrument_element == 'all' or not instrument_element:
                    self.run_every_instruments(instrument_dict, method_name)
                else:
                    logging.info('The instrument: {} has not been found in the autoreduction'
                                 ' database'.format(instrument_element))
        return instrument_dict

    def run_fail_count(self, start_date, end_date):
        """Returns the count of failed runs that have occurred  between two dates."""
        total_runs = DatabaseMonitorChecks.run_count(start_date, self.current_date)
        total_fails = DatabaseMonitorChecks.fail_count(start_date, self.current_date)
        return [total_runs, total_fails]

    @staticmethod
    def failures_per():
        # Returns previous 24 hours of failures with the exception of Monday which returns Friday, Saturday and Sunday

        # Below private functions exist to be called as standalone functions when run manually.
        def _weekend_failures():
            return DatabaseMonitorChecks.get_status_time_period(interval=3)

        def _one_day_failures():
            return DatabaseMonitorChecks.get_status_time_period()

        if date.today().weekday() == 0:  # Returns saturday, sunday and monday
            return _weekend_failures
        else:  # Returns failures within past 24 hours
            return _one_day_failures

    @staticmethod
    def missing_run_numbers_report(instrument_id):

        # returned query format: [number_of_rows, max_rb_number, min_rb_number, [table_list]]
        returned_query = DatabaseMonitorChecks.missing_rb_report(instrument_id)
        reference_list = [item for item in range(returned_query[2],
                                                 returned_query[1] + 1)]  # make ordered list from min_rb to max_rb
        row_range = returned_query[1] - returned_query[2]

        # Shouldn't be possible to have a higher row range than there are rows
        if row_range > returned_query[0]:
            logging.ERROR(
                'bd_state_checks: Row range is larger than row count {} > {}'.format(row_range, returned_query[0]))
        # Means Missing Values are present invoking the need to query which run numbers are missing
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
        # Convert to seconds
        reformat_time = time.strptime(time_format, '%H:%M:%S')
        convert_to_time = datetime.timedelta(hours=reformat_time.tm_hour,
                                             minutes=reformat_time.tm_min,
                                             seconds=reformat_time.tm_sec).total_seconds()
        return convert_to_time

    @staticmethod
    def convert_seconds_to_time(time_in_seconds):
        return str(datetime.timedelta(seconds=time_in_seconds))

    @staticmethod
    def execution_time(self, instruments=None):
        """
        :param instruments: Instrument name taken as input and convert to instrument id
                            - Data type is assumed to ba of type list if not None.

        Returns a dictionary containing one or many instruments as keys containing nested lists of execution times
        """
        # def _execution_time(current_instrument):

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
            for execution_list in list_of_times:
                # Convert time HH:MM:SS into seconds to calculate execution time then converts back to time HH:MM:SS
                time_duration_list = []
                start_end = [execution_list[2], execution_list[3]]
                for time_returned in start_end:
                    # Appends time in seconds to list
                    time_duration_list.append(int(DateInCycle.convert_time_to_seconds(time_returned)))
                # Calculate difference in time
                time_duration = time_duration_list[1] - time_duration_list[0]
                # Converts back ot datetime
                execution = DateInCycle.convert_seconds_to_time(time_duration)
                # Appends execution time to the end of each sublist
                return _append_execution_times(list_of_times, execution)

        # new_start_end_times returned format: [[id, run_number, start_time, end_time], [ ...], ... ]
        new_start_end_times = DatabaseMonitorChecks.run_times(current_instrument)
        return _calc_execution_times(new_start_end_times)
        # DateInCycle.get_query_for_instruments(instruments)

    def execution_time_average(self, instruments):
        """Returns the average execution times of runs between two dates for n instruments
        :param instruments: expects same inout as execution_time - None or list containing string
               'all' or a list of desired instruments"""

        average_execution = {}
        for instrument in self.execution_time(instruments):
            execution_time_count = 0
            for instrument_item in self.execution_time(instruments)[instrument]:
                # Total execution times placed inside var: execution_time_count
                execution_time_in_seconds = instrument_item[4]
                execution_time_count = execution_time_count + execution_time_in_seconds
            # Calculate mean average execution time
            mean_execution = execution_time_count/len(instrument)
            average_execution[instrument] = mean_execution
        return average_execution

    def run_frequency(self):
        """Return run frequencies for N instruments of type: successful run, failed run, or retry run.
        Method output follows the format: Dict {instrument_N : [rpd, tr, rpw, rpw, rpm]}"""
        pass

    def run_frequency_average(self):
        """Returns the run frequency average between two runs."""
        # Return as list

        # return as dataframe
        pass
