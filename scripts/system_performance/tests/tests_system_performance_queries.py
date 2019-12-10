import unittest
from scripts.system_performance.system_performance_queries import DatabaseMonitorChecks

class TestDatabaseMonitorChecks(unittest.TestCase):

    def test_establish_connection(self):
        self.assertEqual(True, False)

    def test_instruments_list(self):
        self.assertEqual(True, False)

    def test_missing_rb_report(self, instrument_id):
        self.assertEqual(True, False)

    def test_run_times(self, instrument):
        self.assertEqual(True, False)

    def test_get_data_by_status_over_time(self, selection=None, status_id=None, retry_run=None, instrument_id=None,
                                     anomic_aphasia=None, end_date=None, interval=None, time_scale=None,
                                     start_date=None):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
