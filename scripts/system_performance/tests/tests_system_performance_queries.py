import unittest
from mock import patch, Mock
from scripts.system_performance.system_performance_queries import DatabaseMonitorChecks
from utils.settings import MYSQL_SETTINGS
from utils.clients.connection_exception import ConnectionException


class MockConnection(Mock):
    pass


class TESTDatabaseMonitorChecks(unittest.TestCase):

    @patch('utils.clients.database_client.DatabaseClient.connect', return_value=MockConnection())
    def setUp(self, _):
        self.mocked_conn_db_mon_checks = DatabaseMonitorChecks()

    def test_valid_init(self):
        self.assertEquals(self.mocked_conn_db_mon_checks.database.credentials, MYSQL_SETTINGS)
        self.assertIsInstance(self.mocked_conn_db_mon_checks.connection, MockConnection)

    @patch('utils.clients.database_client.DatabaseClient.connect')
    def test_invalid_init(self, mock_connect):
        def raise_connection_error():
            raise ConnectionException('database')
        mock_connect.side_effect = raise_connection_error
        self.assertRaises(ConnectionException, DatabaseMonitorChecks)

    def test_query_log_and_execute(self):
        self.mocked_conn_db_mon_checks.query_log_and_execute("test")
        self.mocked_conn_db_mon_checks.connection.execute.called_once_with("test")

    def test_instrument_list(self):
        pass


    #def test_query_log_and_execute(self, constructor_query):


    # def test_instruments_list(self):
    #     list_of_instruments = DatabaseMonitorChecks().instruments_list()
    #
    #     self.assertIsInstance(list_of_instruments, list)
    #
    # def test_missing_rb_report(self):
    #     missing_rb_report = DatabaseMonitorChecks().missing_rb_report(7, start_date='2019:11:12', end_date='2019:12:20')
    #
    #     self.assertIsInstance(missing_rb_report, list)
    #
    # def test_get_data_by_status_over_time(self):
    #     status_over_time = DatabaseMonitorChecks().get_data_by_status_over_time(selection='COUNT(id)', instrument_id=7)
    #
    #     self.assertIsInstance(status_over_time, list)


if __name__ == '__main__':
    unittest.main()
