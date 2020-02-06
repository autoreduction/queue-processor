# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

"""
Test cases for the cycle_webscraper script
"""

import unittest
# import __builtin__
# import sys
# import pandas.util.testing as pdt
# from pandas.util.testing import assert_frame_equal
# import pandas as pd
# from mock import Mock, patch, call

# from scripts.system_performance.cycle_webscraper import TableWebScraper


class TestCycleWebscraper(unittest.TestCase):
    """Test class for web scraper"""

    def setUp(self):
        """Set Up"""
        # print 'setUp'
        # host = 'https://www.isis.stfc.ac.uk/Pages/Beam-Status.aspx'
        # self.web_df = TableWebScraper(host).create_table()
        # self.local_df = TableWebScraper('invalid_url').create_table()
        pass

    def tearDown(self):
        """Tear Down"""
        pass

    @classmethod
    def setUpClass(cls):
        """Set Up"""
        pass

    @classmethod
    def tearDownClass(cls):
        """Tear Down"""
        pass

    def test_save_to_cvs(self):
        """Check file named cycles_dates.csv now exists in current or specified directory"""
        pass

    def test_read_csv(self):
        """Test looking for file if not existent in directory"""
        pass

    def test_create_table(self):
        """ Test if df is of type data frame"""
        pass

# class TestDataClean(unittest.TestCase):
#     """Test Class for cleaning data frame"""

    def test_normalise(self):
        """ Check data frame contains no NAN values and both start
        and end columns are no longer than 10 characters"""
        pass

    def test_month_str_to_int(self):
        """check date is now of numerical format"""
        pass

    def test_date_formatter(self):
        """check date format is off yyyy/mm/dd"""
        # data = pd.read_csv("cycle_dates.csv", encoding='utf-8')
        # test = DataClean.date_formatter(data, 'Start')
        # assert_frame_equal(test, self.local_df['Start'])
        pass
