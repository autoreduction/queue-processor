"""
Attempt to test as much of the windows service as possible
Currently only running unit tests on linux
"""
import unittest
import time
import mock

from mock import patch

from monitors.health_check import HealthCheckThread


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


# pylint:disable=missing-docstring, unused-argument
class TestServiceUtils(unittest.TestCase):

    @mock.patch('monitors.icat_monitor.get_last_run', return_value='1234')
    @mock.patch('monitors.health_check.HealthCheckThread.get_db_client',
                return_value=MockDatabaseClient())
    @mock.patch('monitors.health_check.HealthCheckThread.get_db_last_run',
                return_value=1234)
    def test_health_check_fine(self, last_run, get_db_cli, get_db_run):
        """ Health check where end of run monitor is fine """
        self.assertTrue(HealthCheckThread(0).health_check())
        last_run.assert_called()
        get_db_cli.assert_called()
        get_db_run.assert_called()

    @mock.patch('monitors.icat_monitor.get_last_run', return_value='1231')
    @mock.patch('monitors.health_check.HealthCheckThread.get_db_client',
                return_value=MockDatabaseClient())
    @mock.patch('monitors.health_check.HealthCheckThread.get_db_last_run',
                return_value=1234)
    def test_health_check_old_run(self, last_run, get_db_cli, get_db_run):
        """ Health check where the check returns an old run """
        self.assertTrue(HealthCheckThread(0).health_check())
        last_run.assert_called()
        get_db_cli.assert_called()
        get_db_run.assert_called()

    @mock.patch('monitors.icat_monitor.get_last_run', return_value='1234')
    @mock.patch('monitors.health_check.HealthCheckThread.get_db_client',
                return_value=MockDatabaseClient())
    @mock.patch('monitors.health_check.HealthCheckThread.get_db_last_run',
                return_value=1231)
    def test_health_check_restart(self, last_run, get_db_cli, get_db_run):
        """ Health check where end of run monitor requires a restart """
        self.assertFalse(HealthCheckThread(0).health_check())
        last_run.assert_called_once()
        get_db_cli.assert_called_once()
        get_db_run.assert_called_once()

    @mock.patch('monitors.health_check.HealthCheckThread.last_run_query',
                return_value=MockReductionRun(1234))
    def test_get_db_last_run(self, last_run_mock):
        """ Test to make sure that the last database run is processed correctly """
        db_cli = None
        last_run = HealthCheckThread.get_db_last_run(db_cli, "WISH")
        self.assertEqual(last_run, 1234)

    # pylint:disable=no-self-use
    @mock.patch('utils.clients.database_client.DatabaseClient.__init__', return_value=None)
    @mock.patch('utils.clients.database_client.DatabaseClient.connect', return_value=None)
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

    @mock.patch('monitors.health_check.HealthCheckThread.health_check', return_value=True)
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
