# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Checks if a Date is in a given cycle or not to determine which cycle start and end dates can be used as
validation when running queries and outlining the dates to be used when retrieving statistics giving
an overview of a given cycle.

TODO: Add edge case for maintenance days when issue to format maintenance days column has been completed.
"""


# Dependencies
import datetime

from scripts.system_performance.beam_status_webscraper import Data_Clean, TableWebScraper

# Set url to scrape from, put inside pandas table and clean data frame ready for queries
url = 'https://www.isis.stfc.ac.uk/Pages/Beam-Status.aspx'
df = Data_Clean(TableWebScraper(url).create_table()).normalise()


class DateInCycle:
    """
    :return [current_date, start_date, end_date]
    """

    def __init__(self, data_frame, start_col, end_col, current_date=None):
        self.data_frame = data_frame
        self.start_col = start_col
        self.end_col = end_col

        # By default use today's date if no date has been specified
        if not current_date:
            self.current_date = datetime.date.today()
        else:
            self.current_date = current_date

    @staticmethod
    def cycle_dates(row_index, row):
        """ Return cycle id, start and end elements from a specified row in the Data frame."""
        dates = []
        dates.append(row_index)
        dates.append(row['Start'])
        dates.append(row['End'])
        return dates

    def cycle_search(self, column, row_id):
        """Retrieves a specif row by id from a given dataframe"""
        date_str = self.data_frame.iloc[row_id][column]
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

    def date_in_cycle(self, index, start, end):
        """Actions performed based on current date being inside a cycle or between cycles"""
        out = [False, ['No condition met: \nstart: {} - current: {} - end: {} \nindex: {}'.format(
            start, self.current_date, end, index)]]
        if start <= self.current_date <= end:
            # in cycle
            out = [True, [self.current_date, start, end]]
            # Place future edge case for maintenance days here.
        # Checking row being checked isn't last row
        if index < self.data_frame.tail(1).index.item():
            # In between cycles
            if end < self.current_date > self.cycle_search('Start', index + 1):
                # look at previous cycle
                out = [True,
                       [self.current_date, self.cycle_search('Start', index + 1), self.cycle_search('End', index + 1)]]
            else:
                return out
        else:
            out = 'not last item'
        if index == self.data_frame.tail(1).index.item():
            if self.current_date > start:
                out = [False, [self.current_date, start, end]]
            else:
                out = 'returning oldest accessible cycle'
        return out

    def in_cycle(self):
        """ Check if current date is in or between a cycle and returns a list formatted as:
        [True, input date, cycle start, cycle end] """
        row_iterator = self.data_frame.iterrows()
        point_in_cycle = None

        for i, row in row_iterator:
            cycle = self.cycle_dates(i, row)
            # Convert to datetime object to perform comparisons with.
            cycle[1] = datetime.datetime.strptime(cycle[1], '%Y-%m-%d').date()
            cycle[2] = datetime.datetime.strptime(cycle[2], '%Y-%m-%d').date()
            point_in_cycle = self.date_in_cycle(*cycle)
            if point_in_cycle[0] is True:
                break
        return point_in_cycle[1]


