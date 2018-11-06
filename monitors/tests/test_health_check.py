"""
Attempt to test as much of the windows service as possible
Currently only running unit tests on linux
"""
import unittest
import time

from mock import patch

from monitors.health_check import HealthCheckThread


# pylint:disable=missing-docstring
class TestServiceUtils(unittest.TestCase):

    def test_health_check(self):
        """ This should be updated once health check is fully implemented """
        self.assertTrue(HealthCheckThread(0).health_check())

    def test_stop(self):
        health_check_thread = HealthCheckThread(0)
        self.assertFalse(health_check_thread.exit)
        health_check_thread.stop()
        self.assertTrue(health_check_thread.exit)

    def test_thread_start_stop(self):
        health_check_thread = HealthCheckThread(1)
        health_check_thread.start()
        self.assertTrue(health_check_thread.is_alive())
        health_check_thread.stop()
        # allow some time for the thread to stop
        attempts = 0
        alive = True
        while attempts < 5 and alive is True:
            time.sleep(1)
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
