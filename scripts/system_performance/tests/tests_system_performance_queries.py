# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

"""
Test cases for system_performance_queries script
"""

import unittest
from mock import patch, Mock, MagicMock

from scripts.system_performance.system_performance_queries import DatabaseMonitorChecks
from utils.settings import MYSQL_SETTINGS
from utils.clients.connection_exception import ConnectionException


class MockConnection(Mock):
    """Mock object class"""
    pass


class TESTDatabaseMonitorChecks(unittest.TestCase):
    """Test class for DatabaseMonitorChecks class"""

    def setUp(self):
        """Setup of DatabaseMonitor class call and default arguments dictionary"""
        self.db_monitor_checks = DatabaseMonitorChecks()
        self.arguments_dict = {'selection': 'run_number',
                               'status_id': 4,
                               'retry_run': '',
                               'anomic_aphasia': 'finished',
                               'end_date': 'CURDATE()',
                               'interval': 1,
                               'time_scale': 'DAY',
                               'start_date': None,
                               'instrument_id': None}

    @patch('utils.clients.database_client.DatabaseClient.connect', return_value=MockConnection())
    # pylint: disable=no-value-for-parameter
    # pylint: disable=R0201
    def test_patch_applicator(self, _):
        """Applies patches to method called inside"""
        db_monitor_checks = DatabaseMonitorChecks()
        db_monitor_checks.query_log_and_execute = MagicMock(name='query_log_and_execute')
        return db_monitor_checks

    @patch('utils.clients.database_client.DatabaseClient.connect', return_value=MockConnection())
    # pylint: disable=no-value-for-parameter
    def test_valid_init(self, _):
        """Testing that db_monitor_checks initialization return when valid"""
        db_monitor_checks = DatabaseMonitorChecks()
        self.assertEqual(db_monitor_checks.database.credentials, MYSQL_SETTINGS)
        self.assertIsInstance(db_monitor_checks.connection, MockConnection)

    @patch('utils.clients.database_client.DatabaseClient.connect')
    def test_invalid_init(self, mock_connect):
        """Testing that db initialization return when invalid"""
        def raise_connection_error():
            """Testing expected invalid database connection return"""
            raise ConnectionException('database')
        mock_connect.side_effect = raise_connection_error
        self.assertRaises(ConnectionException, DatabaseMonitorChecks)

    @patch('utils.clients.database_client.DatabaseClient.connect', return_value=MockConnection())
    # pylint: disable=no-value-for-parameter
    # pylint: disable=R0201
    def test_query_log_and_execute(self, _):
        """Testing log and execute method returns expected log and execution of queries passed """
        db_monitor_checks = DatabaseMonitorChecks()
        db_monitor_checks.query_log_and_execute("test")
        db_monitor_checks.connection.execute.called_once_with("test")

    def test_instrument_list(self):
        """Testing that a list of instruments is returned and that index can be cast to int"""
        actual = self.db_monitor_checks.instruments_list()
        expected = ['GEM', 'WISH', 'MUSR']
        actual_instruments = []
        for index, instrument in actual:
            self.assertIsInstance(int(index), int)
            actual_instruments.append(instrument)

        for expected_instrument in expected:
            self.assertIn(expected_instrument, actual_instruments)

    def test_query_sub_segment_replace_intervals(self):
        """Testing appropriate sub segment interval is returned to be inserted in query"""
        # pylint: disable=line-too-long
        expected_intervals = ">= DATE_SUB('{}', INTERVAL {} {})".format(self.arguments_dict['end_date'],
                                                                        self.arguments_dict['interval'],
                                                                        self.arguments_dict['time_scale'])
        actual_intervals = self.db_monitor_checks.query_sub_segment_replace(query_arguments=self.arguments_dict)
        # pylint: enable=line-too-long
        self.assertEqual(expected_intervals, actual_intervals)  # Tests intervals

    def test_query_sub_segment_replace_date_range(self):
        """Testing appropriate sub segment interval is returned to be inserted in query"""
        # pylint: disable=line-too-long
        self.arguments_dict['start_date'], self.arguments_dict['end_date'] = '2019-12-13', '2019-12-12'
        expected_dates_range = "BETWEEN '{}' AND '{}'".format(self.arguments_dict['start_date'],
                                                              self.arguments_dict['end_date'])
        actual_dates_range = self.db_monitor_checks.query_sub_segment_replace(query_arguments=self.arguments_dict)
        # pylint: enable=line-too-long
        self.assertEqual(expected_dates_range, actual_dates_range)        # Tests dates range

    def test_set_date_segment_same_dates(self):
        """Testing appropriate sub-segment interval is returned """
        expected_out = "= '2019-12-13'"
        actual_out = self.db_monitor_checks.set_date_segment(start_date='2019-12-13',
                                                             end_date='2019-12-13')
        self.assertEqual(expected_out, actual_out)  # Tests handling of duplicate dates

    def test_set_date_segment_curdates(self):
        """Testing appropriate sub segment interval is returned to be inserted in query"""
        expected_out = "= 'CURDATE()'"
        # pylint: disable=line-too-long
        actual_out = self.db_monitor_checks.set_date_segment(start_date='CURDATE()',
                                                             end_date=self.arguments_dict['end_date'])
        # pylint: enable=line-too-long
        self.assertEqual(expected_out, actual_out)  # Tests that CURDATE is returned sub segment

    def test_query_segment_replace_no_id(self):
        """Tests that construction of query segment is as expected - No ID set in args"""
        expected_out = [[">= DATE_SUB('CURDATE()'," " INTERVAL 1 DAY)", '']]
        actual = self.db_monitor_checks.query_segment_replace(self.arguments_dict)
        self.assertEqual(expected_out, actual)

    def test_query_segment_replace_id(self):
        """Tests that construction of query segment is as expected - ID set in args"""
        self.arguments_dict['instrument_id'] = 6
        expected_out = [[">= DATE_SUB('CURDATE()', "
                         "INTERVAL 1 DAY)",
                         ', instrument_id']]
        actual = self.db_monitor_checks.query_segment_replace(self.arguments_dict)
        self.assertEqual(expected_out, actual)

    def test_get_data_by_status_over_time(self):
        """Tests that correct query is build - No args set"""
        # pylint: disable=no-value-for-parameter
        db_monitor_checks = self.test_patch_applicator()
        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id ) = (4 )  " \
                   "AND finished >= DATE_SUB('CURDATE()', INTERVAL 1 DAY)"
        db_monitor_checks.get_data_by_status_over_time(**self.arguments_dict)
        db_monitor_checks.query_log_and_execute.called_once_with(expected)

    def test_get_data_by_status_over_time_with_instrument_id(self):
        """Tests that correct query is build -  ID set in args"""
        # pylint: disable=no-value-for-parameter
        db_monitor_checks = self.test_patch_applicator()
        self.arguments_dict['instrument_id'] = 6
        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (4 , 6)  " \
                   "AND finished >= DATE_SUB('CURDATE()', INTERVAL 1 DAY)"
        db_monitor_checks.get_data_by_status_over_time(**self.arguments_dict)
        db_monitor_checks.query_log_and_execute.called_once_with(expected)

    def test_get_data_by_status_over_time_with_date_range(self):
        """Tests that correct query is build - id, start_date and end_date set in args"""
        # pylint: disable=no-value-for-parameter
        db_monitor_checks = self.test_patch_applicator()
        self.arguments_dict['instrument_id'] = 6
        self.arguments_dict['start_date'] = '2019:11:12'
        self.arguments_dict['end_date'] = '2019:11:13'
        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (4 , 6)  " \
                   "AND finished " \
                   "BETWEEN '2019:11:12' AND '2019:12:13'"
        db_monitor_checks.get_data_by_status_over_time(**self.arguments_dict)
        db_monitor_checks.query_log_and_execute.called_once_with(expected)

    def test_get_data_by_status_over_time_with_duplicate_dates(self):
        """Tests that correct query is build - id and duplicate start_date and end_date set"""
        # pylint: disable=no-value-for-parameter
        db_monitor_checks = self.test_patch_applicator()
        self.arguments_dict['instrument_id'] = 6
        self.arguments_dict['start_date'] = '2019:11:12'
        self.arguments_dict['end_date'] = '2019:11:12'
        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (4 , 6)  " \
                   "AND finished = '2019:11:12'"
        db_monitor_checks.get_data_by_status_over_time(**self.arguments_dict)
        db_monitor_checks.query_log_and_execute.called_once_with(expected)

    def test_get_data_by_status_over_time_by_retry(self):
        """Tests that correct query is build - set retry_run arg"""
        # pylint: disable=no-value-for-parameter
        db_monitor_checks = self.test_patch_applicator()
        self.arguments_dict['retry_run'] = 'AND retry_run_id is not null'
        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id ) = (4 ) " \
                   "AND retry_run_id is not null " \
                   "AND finished >= DATE_SUB('CURDATE()', INTERVAL 1 DAY)"
        db_monitor_checks.get_data_by_status_over_time(**self.arguments_dict)
        db_monitor_checks.query_log_and_execute.called_once_with(expected)


if __name__ == '__main__':
    unittest.main()
