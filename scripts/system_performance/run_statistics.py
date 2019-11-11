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
# import logging
# import os
# import sys

# sys.path.append(os.path.join(os.path.dirname(__file__), '../..', 'utils'))
from scripts.system_performance.beam_status_webscraper import Data_Clean, TableWebScraper
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

    def run_fail_count(self, start_date, end_date):
        """Returns the count of failed runs that have occurred  between two dates."""
        total_runs = run_count(start_date, self.current_date)
        total_fails = fail_count(start_date, self.current_date)
        return [total_runs, total_fails]

    def execution_time_average(self):
        """
        Returns the average execution times of runs between two dates
        """
        pass

    def run_frequency_average(self):
        """
        Returns the run frequency average between two runs.
        """
        pass
