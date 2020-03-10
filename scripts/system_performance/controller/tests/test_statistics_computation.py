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

from collections import OrderedDict
from mock import Mock, patch

from scripts.system_performance.controller.statistics_computation import QueryHandler
from scripts.system_performance.models import query_argument_constructor
from scripts.system_performance.test_setup.test_setup_default_mock_variables import SetupVariables


class MockConnection(Mock):
    """Mock object class"""
    pass  # pylint: disable=unnecessary-pass


class TestQueryHandler(unittest.TestCase):
    """Test class encasing all test methods"""

    def setUp(self):
        """ Initial set up of default arguments dictionary"""
        self.arguments_dict = SetupVariables().arguments_dict

    def test_convert_seconds_to_time(self):
        """Assert seconds are converted to datetime"""
        time_in_seconds = 300  # 5 minutes in seconds
        expected = '0:05:00'
        actual = QueryHandler().convert_seconds_to_time(time_in_seconds)

        self.assertEqual(expected, actual)

    def test_convert_time_to_seconds(self):
        """"Assert time formatted is correctly converted into seconds"""
        time_in_minutes = '0:05:00'
        expected = 300
        actual = QueryHandler().convert_time_to_seconds(time_in_minutes)

        self.assertEqual(expected, actual)

    def test_find_missing_numbers_in_list(self):
        """Check that missing numbers a correctly identified in a missing list"""
        list_with_missing_numbers = [1, 2, 4, 5, 7, 9]
        expected = [3, 6, 8]
        actual = QueryHandler().find_missing_numbers_in_list(list_with_missing_numbers)

        self.assertEqual(expected, actual)

    def test_list_zip(self):
        """Assert two lists are correctly zipped together"""
        start_end_times = [['start', 'end'], ['start_1', 'end_1'], ['start_2', 'end_2']]
        execution_times = ['execution', 'execution_1', 'execution_2']
        expected = [['start', 'end', 'execution'],
                    ['start_1', 'end_1', 'execution_1'],
                    ['start_2', 'end_2', 'execution_2']]
        actual = QueryHandler().list_zip(execution_times, start_end_times)

        self.assertEqual(expected, actual)

    def test_list_extraction_and_isolation(self):
        """Assert start and end times have been correctly isolated in seconds"""
        start_end_times = [[66137, 26846, '01:37:17', '01:37:37'],
                           [66153, 26847, '03:49:22', '03:49:45'],
                           [66164, 26848, '05:30:25', '05:30:37']]
        expected = [[5837, 5857], [13762, 13785], [19825, 19837]]
        actual = QueryHandler().list_extraction_and_isolation(start_end_times, 2, 3)

        self.assertEqual(expected, actual)

    def test_nested_lists_to_dict(self):
        """Assert dictionary correctly stores values from execution times sub-lists"""
        list_of_lists = [[66137, 26846, '01:37:17', '01:37:37', '0:00:20'],
                         [66153, 26847, '03:49:22', '03:49:45', '0:00:23']]

        execution_times_dict = QueryHandler().execution_times_dict

        expected = {'execution_time': ['0:00:20', '0:00:23'],
                    'start_time': ['01:37:17', '03:49:22'],
                    'run_number': [26846, 26847],
                    'id': [66137, 66153],
                    'end_time': ['01:37:37', '03:49:45']}
        actual = QueryHandler().nested_lists_to_dict(list_of_lists, execution_times_dict)

        self.assertEqual(expected, actual)

    @patch('scripts.system_performance.models.query_argument_constructor.'
           'runs_in_date_range', autospec=True)
    def test_missing_run_numbers_report_is_dict(self, mock_qle):
        """Assert a dictionary is returned"""

        actual = QueryHandler().missing_run_numbers_report(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date'])

        assert query_argument_constructor.runs_in_date_range(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date']) == mock_qle.return_value

        mock_qle.assert_called_with(self.arguments_dict['instrument_id'],
                                    start_date=self.arguments_dict['start_date'],
                                    end_date=self.arguments_dict['end_date'])

        self.assertIsInstance(actual, dict)

    @patch('scripts.system_performance.models.query_argument_constructor.'
           'runs_in_date_range', autospec=True)
    def test_missing_run_numbers_report_dict_key_count(self, mock_qle):
        """Assert that the method return includes expected number of dictionary keys."""

        actual = QueryHandler().missing_run_numbers_report(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date'])

        assert query_argument_constructor.runs_in_date_range(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date']) == mock_qle.return_value

        self.assertTrue(len(list(actual.keys())), 5)  # Assert number of dictionary keys is 5

    @patch('scripts.system_performance.models.query_argument_constructor.'
           'runs_in_date_range', autospec=True)
    def test_missing_run_numbers_report_assert_expected_return_val(self, mock_qle):
        """Assert a dictionary is returned containing expected missing run number"""

        mock_qle.return_value = [125302, 125303, 125304, 125306]

        actual = QueryHandler().missing_run_numbers_report(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date'])

        assert query_argument_constructor.runs_in_date_range(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date']) == mock_qle.return_value

        expected = [125305]  # Expected missing run
        self.assertEqual(actual['Missing_runs'], expected)

    @patch('scripts.system_performance.models.query_argument_constructor.'
           'start_and_end_times_by_instrument', autospec=True)
    def test_execution_times_is_dict(self, mock_seti):
        """Assert that a dictionary is returned"""

        actual = QueryHandler().execution_times(instrument_id=self.arguments_dict['instrument_id'],
                                                start_date=self.arguments_dict['start_date'],
                                                end_date=self.arguments_dict['end_date'])

        assert query_argument_constructor.start_and_end_times_by_instrument(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date']) == mock_seti.return_value

        self.assertIsInstance(actual, dict)

    @patch('scripts.system_performance.models.query_argument_constructor.'
           'start_and_end_times_by_instrument', autospec=True)
    def test_execution_times_dict_key_count(self, mock_seti):
        """Assert that the length of each list is as expected"""
        mock_seti.return_value = [[68777, 47175, '13:46:59', '13:51:17'],
                                  [68779, 47176, '15:19:00', '15:22:47'],
                                  [68782, 47174, '16:18:59', '16:22:58']]

        actual = QueryHandler().execution_times(instrument_id=self.arguments_dict['instrument_id'],
                                                start_date=self.arguments_dict['start_date'],
                                                end_date=self.arguments_dict['end_date'])

        assert query_argument_constructor.start_and_end_times_by_instrument(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date']) == mock_seti.return_value

        self.assertTrue(len(list(actual.keys())), 4)

    @patch('scripts.system_performance.models.query_argument_constructor.'
           'start_and_end_times_by_instrument', autospec=True)
    def test_execution_times_assert_expected_return_val(self, mock_seti):
        """Assert values returned from db are reformatted correctly"""
        mock_seti.return_value = [[68777, 47175, '13:46:59', '13:51:17'],
                                  [68779, 47176, '15:19:00', '15:22:47'],
                                  [68782, 47174, '16:18:59', '16:22:58']]

        actual = QueryHandler().execution_times(instrument_id=self.arguments_dict['instrument_id'],
                                                start_date=self.arguments_dict['start_date'],
                                                end_date=self.arguments_dict['end_date'])

        assert query_argument_constructor.start_and_end_times_by_instrument(
            instrument_id=self.arguments_dict['instrument_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date']) == mock_seti.return_value

        expected = OrderedDict([('id', [68777, 68779, 68782]),
                                ('run_number', [47175, 47176, 47174]),
                                ('start_time', ['13:46:59', '15:19:00', '16:18:59']),
                                ('end_time', ['13:51:17', '15:22:47', '16:22:58']),
                                ('execution_time', ['0:04:18', '0:03:47', '0:03:59'])])

        self.assertEqual(expected, actual)

    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_day')
    def test_run_frequency_assert_called_rpd(self, mock_rpd):
        """Assert runs per day is called with the correct values"""
        assert query_argument_constructor.runs_per_day(
            instrument_id=self.arguments_dict['instrument_id'],
            status=self.arguments_dict['status_id'],
            retry=self.arguments_dict['retry_run'],
            end_date=self.arguments_dict['end_date']) == mock_rpd.return_value

    @patch('scripts.system_performance.models.query_argument_constructor.runs_today')
    def test_run_frequency_assert_called_rt(self, mock_rt):
        """Assert runs today is called with the correct values"""
        assert query_argument_constructor.runs_today(
            instrument_id=self.arguments_dict['instrument_id'],
            status=self.arguments_dict['status_id'],
            retry=self.arguments_dict['retry_run'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date']) == mock_rt.return_value

    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_week')
    def test_run_frequency_assert_called_rpw(self, mock_rpw):
        """Assert runs per week is called with the correct values"""
        assert query_argument_constructor.runs_per_week(
            instrument_id=self.arguments_dict['instrument_id'],
            status=self.arguments_dict['status_id'],
            retry=self.arguments_dict['retry_run'],
            end_date=self.arguments_dict['end_date'],
            time_interval=self.arguments_dict['interval']) == mock_rpw.return_value

    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_month')
    def test_run_frequency_assert_called_rpm(self, mock_rpm):
        """Assert runs per month is called with the correct values"""
        assert query_argument_constructor.runs_per_month(
            instrument_id=self.arguments_dict['instrument_id'],
            status=self.arguments_dict['status_id'],
            retry=self.arguments_dict['retry_run'],
            end_date=self.arguments_dict['end_date'],
            time_interval=self.arguments_dict['interval']) == mock_rpm.return_value

    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_day')
    @patch('scripts.system_performance.models.query_argument_constructor.runs_today')
    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_week')
    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_month')
    def test_run_frequency_is_dict(self, mock_rpm, mock_rpw, mock_rt, mock_rpd):  # pylint: disable=unused-argument
        """Assert return is of list data type"""

        actual = QueryHandler().run_frequency(
            instrument_id=self.arguments_dict['instrument_id'],
            status=self.arguments_dict['status_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date'])

        self.assertIsInstance(actual, list)

    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_day')
    @patch('scripts.system_performance.models.query_argument_constructor.runs_today')
    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_week')
    @patch('scripts.system_performance.models.query_argument_constructor.runs_per_month')
    def test_run_frequency_dict_key_count(self, mock_rpd, mock_rpt, mock_rpw, mock_rpm):  # pylint: disable=unused-argument
        """Assert that the method return includes expected number of list items."""

        actual = QueryHandler().run_frequency(
            instrument_id=self.arguments_dict['instrument_id'],
            status=self.arguments_dict['status_id'],
            start_date=self.arguments_dict['start_date'],
            end_date=self.arguments_dict['end_date'])

        expected = 4
        self.assertEqual(expected, len(actual))


if __name__ == '__main__':
    unittest.main()
