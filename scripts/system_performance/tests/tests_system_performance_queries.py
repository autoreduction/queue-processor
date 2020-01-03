import unittest
import mock
from scripts.system_performance.system_performance_queries import DatabaseMonitorChecks
from utils.clients.database_client import DatabaseClient


class TESTDatabaseMonitorChecks(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database = DatabaseClient()
        cls.database.connect()
        pass

    def setUp(self):
        self.database = DatabaseClient()
        self.database.connect()
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        pass

    def test_instruments_list(self):
        list_of_instruments = DatabaseMonitorChecks().instruments_list()

        self.assertIsInstance(list_of_instruments, list)

    def test_missing_rb_report(self):
        missing_rb_report = DatabaseMonitorChecks().missing_rb_report(7, start_date='2019:11:12', end_date='2019:12:20')

        self.assertIsInstance(missing_rb_report, list)

    def test_run_times(self):
        run_times = DatabaseMonitorChecks().run_times(7, start_date='2019:11:12', end_date='2019:12:20')

        self.assertIsInstance(run_times, list)

    def test_get_data_by_status_over_time(self):
        status_over_time = DatabaseMonitorChecks().get_data_by_status_over_time(selection='COUNT(id)', instrument_id=7)

        self.assertIsInstance(status_over_time, list)


if __name__ == '__main__':
    unittest.main()
