# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for statistics_computation script
"""

# Dependencies
import unittest
import datetime

from collections import OrderedDict
from mock import Mock, MagicMock

from scripts.system_performance.controller.statistics_computation import QueryHandler


class MockConnection(Mock):
    """Mock object class"""
    pass


class TestQueryHandler(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_convert_seconds_to_time(self):
        """Assert seconds are converted to datetime"""
        time_in_seconds = 300  # 5 minutes in seconds
        expected = '0:05:00'
        actual = QueryHandler().convert_seconds_to_time(time_in_seconds)

        self.assertEqual(expected, actual)

    def test_convert_time_to_seconds(self):
        """"Assert time formatted is correctly converted into seconds"""
        time_in_minutes= '0:05:00'
        expected = 300
        actual = QueryHandler().convert_time_to_seconds(time_in_minutes)

        self.assertEqual(expected, actual)

    def test_find_missing_numbers_in_list(self):
        list_with_missing_numbers = [1, 2, 4, 5, 7, 9]
        expected = [3, 6, 8]
        actual = QueryHandler().find_missing_numbers_in_list(list_with_missing_numbers)

        self.assertEqual(expected, actual)

    def test_list_zip(self):
        start_end_times = [['start', 'end'], ['start_1', 'end_1'], ['start_2', 'end_2']]
        execution_times = ['execution', 'execution_1', 'execution_2']
        expected = [['start', 'end', 'execution'],
                    ['start_1', 'end_1', 'execution_1'],
                    ['start_2', 'end_2', 'execution_2']]
        actual = QueryHandler().list_zip(execution_times, start_end_times)

        self.assertEqual(expected, actual)

    def test_list_extraction_and_isolation(self):
        """assert start and end times have been correctly isolated"""
        start_end_times = [[66137L, 26846L, '01:37:17', '01:37:37'],
                           [66153L, 26847L, '03:49:22', '03:49:45'],
                           [66164L, 26848L, '05:30:25', '05:30:37']]
        expected = [[5837, 5857], [13762, 13785], [19825, 19837]]
        actual = QueryHandler().list_extraction_and_isolation(start_end_times, 2, 3)

        self.assertEqual(expected, actual)

    def test_nested_lists_to_dict(self):
        """Assert dictionary correctly stores values from execution times sub-lists"""
        list_of_lists = [[66137L, 26846L, '01:37:17', '01:37:37', '0:00:20'],
                         [66153L, 26847L, '03:49:22', '03:49:45', '0:00:23']]

        execution_times_dict = OrderedDict()
        execution_times_dict['id'] = []
        execution_times_dict['run_number'] = []
        execution_times_dict['start_time'] = []
        execution_times_dict['end_time'] = []
        execution_times_dict['execution_time'] = []

        expected = {'execution_time': ['0:00:20', '0:00:23'],
                    'start_time': ['01:37:17', '03:49:22'],
                    'run_number': [26846L, 26847L],
                    'id': [66137L, 66153L],
                    'end_time': ['01:37:37', '03:49:45']}
        actual = QueryHandler().nested_lists_to_dict(list_of_lists, execution_times_dict)

        self.assertEqual(expected, actual)

    def test_missing_run_numbers_report(self):
        """Assert a dictionary is returned containing:
        [count of run run number between two dates/time,
         the count of missing run numbers,
         [nested list of missing run numbers id's]]"""
        # will need to mock
        pass

    def test_execution_times(self):

        # will need to mock
        pass

    def test_run_frequency(self):

        # will need to  mock
        pass


if __name__ == '__main__':
    unittest.main()