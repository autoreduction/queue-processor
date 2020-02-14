import unittest

# from datetime import datetime, date
import datetime

from mock import patch, Mock, MagicMock

from scripts.system_performance.models import query_argument_constructor
from scripts.system_performance.data_persistence.system_performance_queries import DatabaseMonitorChecks


class MockConnection(Mock):
    """Mock object class"""
    pass


class TestQueryArgumentsConstructor(unittest.TestCase):
    """"""

    def setUp(self):
        self.db_monitor_checks = DatabaseMonitorChecks()

        self.arguments_dict = {'selection': 'run_number',
                               'status_id': 4,
                               'retry_run': '',
                               'run_state_column': 'finished',
                               'end_date': 'CURDATE()',
                               'interval': 1,
                               'time_scale': 'DAY',
                               'start_date': None,
                               'instrument_id': None}

    @staticmethod
    def mock_datetime_today(target, dt):
        real_datetime_class = datetime.datetime

        class DatetimeSubclassMeta(type):
            @classmethod
            def __instancecheck__(mcs, obj):
                return isinstance(obj, real_datetime_class)

        class BaseMockedDatetime(real_datetime_class):
            @classmethod
            def today(cls, tz=None):
                return target.replace(tzinfo=tz)

        # Python2 & Python3 compatible metaclass
        MockedDatetime = DatetimeSubclassMeta('datetime', (BaseMockedDatetime,), {})

        return patch.object(dt, 'datetime', MockedDatetime)

    @patch('utils.clients.database_client.DatabaseClient.connect', return_value=MockConnection())
    # pylint: disable=no-value-for-parameter, no-self-use
    def test_patch_applicator(self, _):
        """Applies patches to method called inside"""
        db_monitor_checks = DatabaseMonitorChecks()
        db_monitor_checks.query_log_and_execute = MagicMock(name='query_log_and_execute')
        return db_monitor_checks

    def test_get_list_of_instruments(self):
        """Assert that a list of instruments is returned """
        actual = query_argument_constructor.get_list_of_instruments()
        expected = ['GEM', 'WISH', 'MUSR']
        actual_instruments = []
        for index, instrument in actual:
            self.assertIsInstance(int(index), int)
            actual_instruments.append(instrument)

        for expected_instrument in expected:
            self.assertIn(expected_instrument, actual_instruments)

    def test_missing_run_numbers_constructor(self):
        """Assert number of lists is 4"""
        pass

    @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')
    def test_start_and_end_times_by_instrument(self, mock_qle):

        expected = "SELECT id, run_number, " \
                   "DATE_FORMAT(started, '%H:%i:%s') TIMEONLY, " \
                   "DATE_FORMAT(finished, '%H:%i:%s') TIMEONLY " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (4 , 4)  " \
                   "AND created BETWEEN '2019-12-12' AND '2019-12-14'"

        query_argument_constructor.start_and_end_times_by_instrument(4, '2019-12-12', '2019-12-14')

        mock_qle.assert_called_once_with(expected)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')
    def test_runs_per_day(self, mock_qle):

        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (1 , 4)  " \
                   "AND finished >= DATE_SUB('2019-12-14', INTERVAL 1 DAY)"

        query_argument_constructor.runs_per_day(instrument_id=4,
                                                status=1,
                                                retry='',
                                                end_date='2019-12-14')

        mock_qle.assert_called_once_with(expected)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')
    def test_runs_today(self, mock_qle):

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

    @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')
    def test_runs_per_week_friday(self, mock_rpw):
        """"""
        #  TODO add mock for runs_per_week return
        # mock datetime

        expected = "SELECT run_number " \
                   "FROM reduction_viewer_reductionrun " \
                   "WHERE (status_id , instrument_id) = (4 , 9)  " \
                   "AND finished >= DATE_SUB('2020-2-7', INTERVAL 1 WEEK)"

        target = datetime.datetime(2020, 2, 7)
        # with patch.object(datetime, 'datetime', Mock(wraps=datetime.datetime)) as patched:
        with self.mock_datetime_today(target, datetime):
            # patched.today.return_value = target
            # print(datetime.datetime.today().weekday())
            # print(isinstance(datetime.datetime.now(), datetime.datetime))
            query_argument_constructor.runs_per_week(instrument_id=9,
                                                     status=4,
                                                     retry='',
                                                     end_date='2020-2-7',
                                                     time_interval=1)

            mock_rpw.assert_called_once_with(expected)
        # pass



   # patch('scripts.system_performance.models.query_argument_constructor.runs_per_week') as mock_date:
   #          mock_date.today.return_value = date(2020, 2, 7)
   #          mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
   #
   #          assert query_argument_constructor.runs_per_week.date.today() == date(2020, 2, 7)

        pass

    def test_runs_per_week_not_friday(self):

        pass

    def test_runs_per_month_end_of_month(self):

        pass

    def test_runs_per_month_not_end_of_month(self):

        pass


if __name__ == '__main__':
    unittest.main()
