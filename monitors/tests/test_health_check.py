"""
Attempt to test as much of the windows service as possible
Currently only running unit tests on linux
"""
import unittest
import time
import csv
import os
import mock

from monitors.health_check import HealthCheckThread
from monitors.end_of_run_monitor import write_last_run
from monitors.settings import EORM_LAST_RUN_FILE


def create_runs_csv():
    """
    Create a test runs CSV file
    """
    write_last_run(EORM_LAST_RUN_FILE, 'GEM', '1234')
    write_last_run(EORM_LAST_RUN_FILE, 'WISH', '1234')
    write_last_run(EORM_LAST_RUN_FILE, 'POLARIS', '1234')


# pylint:disable=missing-docstring, unused-argument
class TestServiceUtils(unittest.TestCase):

    @classmethod
    def setUp(cls):
        create_runs_csv()

    @mock.patch('monitors.icat_monitor.get_last_run', return_value='1234')
    def test_health_check_fine(self, last_run):
        """ Health check where end of run monitor is fine """
        self.assertTrue(HealthCheckThread(0).health_check())

    @mock.patch('monitors.icat_monitor.get_last_run', return_value='1233')
    def test_health_check_old_run(self, last_run):
        """ Health check where the check returns an old run """
        self.assertTrue(HealthCheckThread(0).health_check())

    @mock.patch('monitors.icat_monitor.get_last_run', return_value='1235')
    def test_health_check_restart(self, last_run):
        """ Health check where end of run monitor requires a restart """
        self.assertFalse(HealthCheckThread(0).health_check())

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
