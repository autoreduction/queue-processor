import unittest
from mock import patch, Mock

from scripts.system_performance.system_performance_queries import DatabaseMonitorChecks
from utils.settings import MYSQL_SETTINGS
from utils.clients.connection_exception import ConnectionException


class MockConnection(Mock):
    pass


class TESTDatabaseMonitorChecks(unittest.TestCase):


    def setUp(self):
       self.db = DatabaseMonitorChecks()
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
    def test_valid_init(self, _):
        db = DatabaseMonitorChecks()
        self.assertEquals(db.database.credentials, MYSQL_SETTINGS)
        self.assertIsInstance(db.connection, MockConnection)

    @patch('utils.clients.database_client.DatabaseClient.connect')
    def test_invalid_init(self, mock_connect):
        def raise_connection_error():
            raise ConnectionException('database')
        mock_connect.side_effect = raise_connection_error
        self.assertRaises(ConnectionException, DatabaseMonitorChecks)

    @patch('utils.clients.database_client.DatabaseClient.connect', return_value=MockConnection())
    def test_query_log_and_execute(self, _):
        db = DatabaseMonitorChecks()
        db.query_log_and_execute("test")
        db.connection.execute.called_once_with("test")

    def test_instrument_list(self):
        actual = self.db.instruments_list()
        expected = ['GEM', 'WISH', 'MUSR']
        actual_instruments = []
        for index, instrument in actual:
            self.assertIsInstance(index, long)
            actual_instruments.append(instrument)

        for expected_instrument in expected:
            self.assertIn(expected_instrument, actual_instruments)

    def test_query_sub_segment_replace_intervals(self):
        expected_intervals = ">= DATE_SUB('{}', INTERVAL {} {})".format(self.arguments_dict['end_date'],
                                                                        self.arguments_dict['interval'],
                                                                        self.arguments_dict['time_scale'])
        actual_intervals = self.db.query_sub_segment_replace(query_arguments=self.arguments_dict)

        # tests intervals
        self.assertEqual(expected_intervals, actual_intervals)

    def test_query_sub_segment_replace_date_range(self):
        self.arguments_dict['start_date'], self.arguments_dict['end_date'] = '2019-12-13', '2019-12-12'
        expected_dates_range = "BETWEEN '{}' AND '{}'".format(self.arguments_dict['start_date'],
                                                              self.arguments_dict['end_date'])
        actual_dates_range = self.db.query_sub_segment_replace(query_arguments=self.arguments_dict)

        # tests dates range
        self.assertEqual(expected_dates_range, actual_dates_range)

    def test_set_date_segment_same_dates(self):
        expected_out = '= 2019-12-13'
        actual_out = self.db.set_date_segment(start_date='2019-12-13', end_date='2019-12-13')
        self.assertEqual(expected_out, actual_out)

    def test_set_date_segment_curdates(self):
        expected_out = '= CURDATE()'
        actual_out = self.db.set_date_segment(start_date='CURDATE()', end_date='CURDATE()')
        self.assertEqual(expected_out, actual_out)

    def test_query_segment_replace_no_id(self):
        expected_out = [[">= DATE_SUB('CURDATE()', INTERVAL 1 DAY)", '']]
        actual = self.db.query_segment_replace(self.arguments_dict)
        self.assertEqual(expected_out, actual)

    def test_query_segment_replace_id(self):
        self.arguments_dict['instrument_id'] = 6
        expected_out = [[">= DATE_SUB('CURDATE()', INTERVAL 1 DAY)", ', instrument_id']]
        actual = self.db.query_segment_replace(self.arguments_dict)
        self.assertEqual(expected_out, actual)

    # def test_query_segment_replace_no_instrument_id(self):
    #     pass
    #
    # def test_query_segment_replace_instrument_id(self):
    #     self.arguments_dict['instrument_id'] = 4
    #     pass


    #def test_query_log_and_execute(self, constructor_query):


    # def test_instruments_list(self):
    #     list_of_instruments = DatabaseMonitorChecks().instruments_list()
    #
    #     self.assertIsInstance(list_of_instruments, list)
    #
    # def test_missing_rb_report(self):
    #     rb_range_by_instrument = DatabaseMonitorChecks().rb_range_by_instrument(7, start_date='2019:11:12', end_date='2019:12:20')
    #
    #     self.assertIsInstance(rb_range_by_instrument, list)
    #
    # def test_get_data_by_status_over_time(self):
    #     status_over_time = DatabaseMonitorChecks().get_data_by_status_over_time(selection='COUNT(id)', instrument_id=7)
    #
    #     self.assertIsInstance(status_over_time, list)


if __name__ == '__main__':
    unittest.main()
