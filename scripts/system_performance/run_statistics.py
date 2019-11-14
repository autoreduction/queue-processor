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
            #Edge case for current date not in a cycle or between cycles (covers maintenance days when added)
            else:
                in_cycle = None
                return in_cycle
        # Looking at last row in data frame. Current date can't be checked any further back in time
        else:
            in_cycle = None
            return in_cycle

    @staticmethod
    def list_all_instruments():
        instrument_list = DatabaseMonitorChecks.list_instruments()
        return instrument_list

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
    def missing_run_numbers_report(self):

        # returned query format: [number_of_rows, max_rb_number, min_rb_number, [table_list]]
        returned_query = DatabaseClient.missing_rb_report()
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
    def execution_time(instruments=None):
        """
        :param instruments: Instrument name taken as input and convert to instrument id
                            - Data type is assumed to ba of type list if not None.

        Returns a dictionary containing one or many instruments as keys containing nested lists of execution times
        """
        def _execution_time(current_instrument):

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

            def _calc_execution_times(start_end_times):
                for execution_list in start_end_times:
                    # Convert time HH:MM:SS into seconds to calculate execution time then converts back to time HH:MM:SS
                    time_duration_list = []
                    start_end = [execution_list[2], execution_list[3]]
                    for time_returned in start_end:
                        # Convert to seconds
                        reformat_time = time.strptime(time_returned, '%H:%M:%S')
                        convert_to_time = datetime.timedelta(hours=reformat_time.tm_hour,
                                                             minutes=reformat_time.tm_min,
                                                             seconds=reformat_time.tm_sec).total_seconds()
                        # Appends to list
                        time_duration_list.append(int(convert_to_time))
                    # Calculate difference in time
                    time_duration = time_duration_list[1] - time_duration_list[0]
                    # Converts back ot datetime
                    execution = str(datetime.timedelta(seconds=time_duration))
                    # Appends execution time to the end of each sublist
                    return _append_execution_times(start_end_times, execution)

            # start_end_times returned format: [[id, run_number, start_time, end_time], [ ...], ... ]
            start_end_times = DatabaseMonitorChecks.run_times(current_instrument)

            return _calc_execution_times(start_end_times)

        def input_verification(instrument_input):
            # look through all instrument items formatted as: [instrument_id, instrument_name]
            # Checking n instruments in input to see if they exist and handling accordingly.
            instrument_dict = {}
            for sublist in DateInCycle.list_all_instruments():
                if not instrument_input:
                    # run all instruments
                    return run_every_instruments(instrument_dict)
                for instrument in instrument_input:
                    if sublist == instrument:
                        # Dict has the format: "instrument name" : [[id, rb_number , start, end, execution_time ][...]]
                        instrument_dict[sublist[1]] = _execution_time(sublist[0])
                        break
                    elif instrument == 'all':
                        # run all instruments
                        return run_every_instruments(instrument_dict)
                    else:
                        logging.error('The instrument: {} is not currently using Autoreduction'.format(instrument))
                        break

        def run_every_instruments(instrument_dict):
            """returns all instruments and executions times in a dictionary : instrument_name : execution time"""
            for sublist in DateInCycle.list_all_instruments():
                instrument_dict[sublist[1]] = _execution_time(sublist[0])
            return instrument_dict

        return input_verification(instruments)

    def execution_time_average(self):
        """Returns the average execution times of runs between two dates for n instruments"""

        pass

    def run_frequency_average(self):
        """Returns the run frequency average between two runs."""

        pass
