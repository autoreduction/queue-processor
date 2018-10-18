"""
Attempt to test as much of the windows service as possible
Currently only running unit tests on linux
"""
import unittest

from monitors.monitor_win_service import health_check


class TestWinService(unittest.TestCase):

    def test_health_check(self):
        """ This should be updated once health check is fully implemented """
        self.assertTrue(health_check())
