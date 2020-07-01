# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for the timeout helper class
"""
import unittest
import os
import signal

from mock import patch

from queue_processors.autoreduction_processor.timeout import TimeOut


# pylint:disable=missing-docstring
class TestTimeOut(unittest.TestCase):

    def setUp(self):
        self.timeout = TimeOut(seconds=10,
                               error_message='test error message')

    def test_init(self):
        self.assertEqual(self.timeout.seconds, 10)
        self.assertEqual(self.timeout.error_message, 'test error message')

    def test_handle_timeout(self):
        self.assertRaises(Exception, self.timeout.handle_timeout)

    # Add no cover to keep windows coverage happy
    if os.name != 'nt':  # pragma: no cover
        @patch('signal.signal')
        @patch('signal.alarm')
        def test_enter(self, mock_alarm, mock_signal):
            self.timeout.__enter__()
            mock_signal.assert_called_once_with(signal.SIGALRM,  # pylint:disable=no-member
                                                self.timeout.handle_timeout)
            mock_alarm.assert_called_once_with(10)

        @patch('signal.alarm')
        def test_exit(self, mock_alarm):
            self.timeout.__exit__('test', 'test', 'test')
            mock_alarm.assert_called_once_with(0)
