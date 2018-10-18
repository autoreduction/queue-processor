"""
Attempt to test as much of the windows service as possible
Currently only running unit tests on linux
"""
import unittest
import time

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
