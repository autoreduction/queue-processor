"""
Attempt to test as much of the windows service as possible
Currently only running unit tests on linux
"""
import json
import unittest
import time

from mock import patch, call, Mock

from monitors.health_check import HealthCheckThread
from utils.clients.connection_exception import ConnectionException


# pylint:disable=too-few-public-methods
class MockReductionRun(object):
    """
    Mock representing a row in the reduction run database
    """
    def __init__(self, run_num):
        self.run_number = run_num


# pylint:disable=missing-docstring
class MockDatabaseClient(object):
    """
    Mock representing a database client
    """
    @staticmethod
    def disconnect():
        return None

    @staticmethod
    def connect():
        return None


# pylint:disable=missing-docstring, unused-argument, invalid-name
class TestServiceUtils(unittest.TestCase):

    @patch('monitors.icat_monitor.icat_login')
    @patch('monitors.icat_monitor.get_last_run', return_value=1234)
    @patch('monitors.health_check.HealthCheckThread.get_db_client',
           return_value=MockDatabaseClient())
    @patch('monitors.health_check.HealthCheckThread.get_db_last_run',
           return_value=1234)
    def test_health_check_fine(self, last_run, get_db_cli, get_db_run, icat_login):
        """ Health check where end of run monitor is fine """
        self.assertTrue(HealthCheckThread(0).health_check())
        icat_login.assert_called_once()
        last_run.assert_called()
        get_db_cli.assert_called()
        get_db_run.assert_called()

    @patch('monitors.icat_monitor.icat_login')
    @patch('monitors.icat_monitor.get_last_run', return_value=1231)
    @patch('monitors.health_check.HealthCheckThread.get_db_client',
           return_value=MockDatabaseClient())
    @patch('monitors.health_check.HealthCheckThread.get_db_last_run',
           return_value=1234)
    def test_health_check_old_run(self, last_run, get_db_cli, get_db_run, icat_login):
        """ Health check where the check returns an old run """
        self.assertTrue(HealthCheckThread(0).health_check())
        icat_login.assert_called_once()
        last_run.assert_called()
        get_db_cli.assert_called()
        get_db_run.assert_called()

    @patch('monitors.icat_monitor.icat_login')
    @patch('monitors.icat_monitor.get_last_run', return_value=1234)
    @patch('monitors.health_check.HealthCheckThread.get_db_client',
           return_value=MockDatabaseClient())
    @patch('monitors.health_check.HealthCheckThread.get_db_last_run',
           return_value=1231)
    @patch('monitors.health_check.HealthCheckThread.resubmit_run')
    def test_health_check_restart(self, _, last_run, get_db_cli, get_db_run, icat_login):
        """
        Health check where end of run monitor requires a restart
        Mock the resubmit call to avoid having to perform extra test setup
        """
        self.assertFalse(HealthCheckThread(0).health_check())
        icat_login.assert_called_once()
        last_run.assert_called_once()
        get_db_cli.assert_called_once()
        get_db_run.assert_called_once()

    @patch('monitors.health_check.HealthCheckThread.last_run_query',
           return_value=MockReductionRun(1234))
    def test_get_db_last_run(self, last_run_mock):
        """ Test to make sure that the last database run is processed correctly """
        db_cli = None
        last_run = HealthCheckThread.get_db_last_run(db_cli, "WISH")
        last_run_mock.assert_called_once()
        self.assertEqual(last_run, 1234)

    @patch('monitors.health_check.HealthCheckThread.last_run_query',
           return_value=None)
    def test_get_db_last_run_no_runs(self, last_run_mock):
        db_cli = None
        last_run = HealthCheckThread.get_db_last_run(db_cli, 'WISH')
        last_run_mock.assert_called_once()
        self.assertIsNone(last_run)

    # pylint:disable=no-self-use
    @patch('utils.clients.database_client.DatabaseClient.__init__', return_value=None)
    @patch('utils.clients.database_client.DatabaseClient.connect', return_value=None)
    def test_get_db_client(self, db_cli_init, db_cli_connect):
        """ Test to ensure the database client is retrieved correctly """
        HealthCheckThread.get_db_client()
        db_cli_init.assert_called_once()
        db_cli_connect.assert_called_once()

    def test_stop(self):
        health_check_thread = HealthCheckThread(0)
        self.assertFalse(health_check_thread.exit)
        health_check_thread.stop()
        self.assertTrue(health_check_thread.exit)

    @patch('monitors.health_check.HealthCheckThread.health_check', return_value=True)
    def test_thread_start_stop(self, health_check_mock):
        health_check_thread = HealthCheckThread(1)
        health_check_thread.start()
        self.assertTrue(health_check_thread.is_alive())
        health_check_thread.stop()
        # allow some time for the thread to stop
        attempts = 0
        alive = True
        while attempts < 5 and alive is True:
            time.sleep(2)
            alive = health_check_thread.is_alive()
            attempts += 1
        self.assertFalse(alive)

    # pylint:disable=no-self-use
    @patch('monitors.end_of_run_monitor.stop')
    @patch('monitors.end_of_run_monitor.main')
    def test_restart(self, mock_eorm_start, mock_eorm_stop):
        """
        Ensure that restart calls the main(start) and stop functions of the End of Run Monitor
        """
        health_check_thread = HealthCheckThread(0)
        health_check_thread.restart_service()
        mock_eorm_start.assert_called_once()
        mock_eorm_stop.assert_called_once()

    # pylint:disable=no-self-use
    @patch('monitors.health_check.HealthCheckThread.restart_service')
    @patch('monitors.health_check.HealthCheckThread.health_check', return_value=False)
    def test_service_problem(self, health_check_mock, restart_service_mock):
        """
        Ensure that the restart service has been called if the heath check returns false
        """
        health_check_thread = HealthCheckThread(2)
        health_check_thread.start()
        time.sleep(1)
        health_check_mock.assert_called_once()
        restart_service_mock.assert_called_once()
        health_check_thread.exit = True

    @patch('monitors.icat_monitor.get_file_rb_and_location', return_value=("123", "GEM555.nxs"))
    @patch('utils.clients.queue_client.QueueClient.send')
    def test_resubmit_run(self, mock_send, mock_get_file_loc):
        """
        Ensure that runs are resubmitted correct using the queue client send function
        """
        icat_client = Mock()
        HealthCheckThread.resubmit_run(icat_client, 'GEM', '555')
        expected_message = {'rb_number': '123',
                            'instrument': 'GEM',
                            'data': 'GEM555.nxs',
                            'run_number': '555',
                            'facility': 'ISIS'
                           }
        mock_send.assert_called_once_with('/queue/DataReady', json.dumps(expected_message))
        mock_get_file_loc.assert_called_once_with(icat_client, 'GEM', '555')

    @patch('monitors.icat_monitor.get_file_rb_and_location', return_value=(None, None))
    @patch('logging.error')
    def test_resubmit_unable_to_find_run(self, mock_error_log, mock_get_file_loc):
        icat_client = Mock()
        self.assertFalse(HealthCheckThread.resubmit_run(icat_client, 'GEM', '555'))
        mock_error_log.assert_called_once_with('Unable to find RB number for run: %s%s',
                                               'GEM', '555')
        mock_get_file_loc.assert_called_once_with(icat_client, 'GEM', '555')

    @patch('logging.error')
    @patch('utils.clients.queue_client.QueueClient.connect')
    def test_resubmit_with_invalid_queue_connection(self, mock_connect, mock_error_log):
        def raise_connection_exp():
            raise ConnectionException('test')
        mock_connect.side_effect = raise_connection_exp
        icat_client = Mock()
        self.assertFalse(HealthCheckThread.resubmit_run(icat_client, 'GEM', '555'))
        mock_error_log.assert_called_once_with('Unable to connect to Queue')

    @patch('monitors.health_check.HealthCheckThread.get_db_last_run', return_value=10)
    @patch('monitors.icat_monitor.icat_login', return_value=None)
    @patch('monitors.icat_monitor.get_last_run', return_value=13)
    @patch('monitors.health_check.HealthCheckThread.resubmit_run')
    def test_resubmit_from_health_check(self, mock_resubmit, mock_icat_last_run,
                                        mock_icat_login, mock_get_last_run):
        self.assertFalse(HealthCheckThread.health_check())
        mock_icat_login.assert_called_once()
        mock_get_last_run.assert_called_once()
        mock_icat_last_run.assert_called_once()
        expected_calls = [call(None, 'WISH', 10),
                          call(None, 'WISH', 11),
                          call(None, 'WISH', 12),
                          call(None, 'WISH', 13)]
        mock_resubmit.assert_has_calls(expected_calls)
