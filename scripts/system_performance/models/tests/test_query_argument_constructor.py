# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""Unit tests  for scripts/system_performance/models/query_argument_constructor.py"""
import unittest

from datetime import date
from mock import patch, Mock

from scripts.system_performance.models import query_argument_constructor
# pylint:disable=line-too-long
from scripts.system_performance.data_persistence.system_performance_queries import DatabaseMonitorChecks  # pylint: disable=line-too-long
from scripts.system_performance.test_setup.test_setup_default_mock_variables import SetupVariables


class MockConnection(Mock):
    """Mock object class"""
    pass # pylint: disable=W0107


class TestQueryArgumentsConstructor(unittest.TestCase):
    """Unit tests for query argument constructor class methods"""

    def setUp(self):
        """Initial setup of default query argument dictionary """
        self.db_monitor_checks = DatabaseMonitorChecks()

        self.arguments_dict = SetupVariables().arguments_dict

    def test_get_day_of_week_invalid(self):
        """Testing invalid day of week"""
        invalid = 10
        actual = query_argument_constructor.get_day_of_week()
        self.assertNotEqual(invalid, actual)

    def test_get_day_of_week_valid(self):
        """Testing valid day of week"""
        expected = date.today()
        actual = query_argument_constructor.get_day_of_week()
        self.assertEqual(expected, actual)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.'
           'DatabaseMonitorChecks.get_instruments_from_database')
    def test_get_instruments(self, mock_gid):
        """Assert that a list of instruments is returned """
        query_argument_constructor.get_instruments()

        self.assertTrue(mock_gid.called)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.'
           'DatabaseMonitorChecks.query_log_and_execute')  # pylint: disable=no-self-use
    def test_runs_in_date_range(self, mock_qle):
        """Assert number of lists is 4"""

        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE instrument_id = 8 " \
                   "AND created " \
                   "BETWEEN '2020-02-17' AND '2020-02-19'"

        query_argument_constructor.runs_in_date_range(8, '2020-02-17', '2020-02-19')

        mock_qle.assert_called_once_with(expected)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.'
           'DatabaseMonitorChecks.query_log_and_execute')  # pylint: disable=no-self-use
    def test_start_and_end_times_by_instrument(self, mock_qle):
        """ Assert that query is called with correct arguments"""
        expected = "SELECT id, run_number, " \
                   "DATE_FORMAT(started, '%H:%i:%s') TIMEONLY, " \
                   "DATE_FORMAT(finished, '%H:%i:%s') TIMEONLY " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (4 , 4)  " \
                   "AND created BETWEEN '2019-12-12' AND '2019-12-14'"

        query_argument_constructor.start_and_end_times_by_instrument(4, '2019-12-12', '2019-12-14')

        mock_qle.assert_called_once_with(expected)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.'
           'DatabaseMonitorChecks.query_log_and_execute')  # pylint: disable=no-self-use
    def test_runs_per_day(self, mock_qle):
        """ Assert runs per day query is called with correct arguments"""
        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (1 , 4)  " \
                   "AND finished >= DATE_SUB('2019-12-14', INTERVAL 1 DAY)"

        query_argument_constructor.runs_per_day(instrument_id=4,
                                                status=1,
                                                retry='',
                                                end_date='2019-12-14')

        mock_qle.assert_called_once_with(expected)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.'
           'DatabaseMonitorChecks.query_log_and_execute')  # pylint: disable=no-self-use
    def test_runs_today(self, mock_qle):
        """Test the runs today query is constructed as expected"""
        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (4 , 9)  " \
                   "AND finished " \
                   "BETWEEN '2019-12-12' AND '2019-12-14'"

        query_argument_constructor.runs_today(instrument_id=9,
                                              status=4,
                                              retry='',
                                              start_date='2019-12-12',
                                              end_date='2019-12-14')

        mock_qle.assert_called_once_with(expected)

    @patch('scripts.system_performance.models.query_argument_constructor.get_day_of_week') # pylint: disable=no-self-use, line-too-long
    def test_runs_per_week_not_friday(self, mock_gdw):
        """ Test runs per week when the day of the week is NOT friday"""
        # mock datetime
        todays_date = '2020-02-13'
        mock_gdw.return_value = date(*map(int, todays_date.split('-')))

        actual = query_argument_constructor.runs_per_week(instrument_id=1,
                                                          status=4,
                                                          retry='',
                                                          end_date='2020-2-13',
                                                          time_interval=1)
        self.assertEqual(None, actual)

    # pylint: disable=no-self-use
    @patch('scripts.system_performance.data_persistence.system_performance_queries.'
           'DatabaseMonitorChecks.get_data_by_status_over_time')
    @patch('scripts.system_performance.models.query_argument_constructor.get_day_of_week')
    # pylint: enable=no-self-use
    def test_runs_per_week_friday(self, mock_gdw, mock_gdsot):
        """ Test runs per week when the day of the week IS Friday"""
        # mock datetime
        todays_date = '2020-02-14'
        mock_gdw.return_value = date(*map(int, todays_date.split('-')))
        mock_gdsot.return_value = 'Friday!'

        actual = query_argument_constructor.runs_per_week(instrument_id=1,
                                                          status=4,
                                                          retry='',
                                                          end_date='2020-2-14',
                                                          time_interval=1)

        mock_gdsot.assert_called_once_with(instrument_id=1,
                                           status_id=4,
                                           retry_run='',
                                           end_date='2020-2-14',
                                           interval=1,
                                           time_scale='WEEK')
        self.assertEqual('Friday!', actual)

    # pylint: disable=no-self-use
    @patch('scripts.system_performance.data_persistence.system_performance_queries.'
           'DatabaseMonitorChecks.get_data_by_status_over_time')
    @patch('scripts.system_performance.models.query_argument_constructor.get_day_of_week')
    # pylint: enable=no-self-use
    def test_runs_per_month_end_of_month(self, mock_gdw, mock_gdsot):
        """ Assert expected return value is returned if day is last day of month"""

        todays_date = '2020-02-29'
        mock_gdw.return_value = date(*map(int, todays_date.split('-')))
        mock_gdsot.return_value = 'End of month'

        actual = query_argument_constructor.runs_per_month(instrument_id=1,
                                                           status=4,
                                                           retry='',
                                                           end_date='2020-03-29',
                                                           time_interval=1)

        mock_gdsot.assert_called_once_with(instrument_id=1,
                                           status_id=4,
                                           retry_run='',
                                           end_date='2020-03-29',
                                           interval=1,
                                           time_scale='MONTH')
        print('test')
        self.assertEqual('End of month', actual)

    # pylint: disable=no-self-use
    @patch('scripts.system_performance.data_persistence.system_performance_queries.'
           'DatabaseMonitorChecks.get_data_by_status_over_time')
    @patch('scripts.system_performance.models.query_argument_constructor.get_day_of_week')
    # pylint: enable=no-self-use
    def test_runs_per_month_not_end_of_month(self, mock_gdw, mock_gdsot):
        """ Assert that method returns non if date is not equivalent to end of month"""

        todays_date = '2020-02-14'
        mock_gdw.return_value = date(*map(int, todays_date.split('-')))

        mock_gdsot.return_value = 'End of month'

        actual = query_argument_constructor.runs_per_month(instrument_id=1,
                                                           status=4,
                                                           retry='',
                                                           end_date='2020-02-14',
                                                           time_interval=1)
        self.assertEqual(None, actual)


if __name__ == '__main__':
    unittest.main()
