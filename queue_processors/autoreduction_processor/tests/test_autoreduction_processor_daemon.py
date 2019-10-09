# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for the Autoreduction Processor daemon thread
"""
import unittest
import sys

from mock import patch, call

from queue_processors.autoreduction_processor.\
    autoreduction_processor_daemon import main


# pylint:disable=missing-docstring,no-self-use
class TestAutoreductionProcessorDaemon(unittest.TestCase):

    @patch('queue_processors.daemon.Daemon.start')
    @patch('sys.exit')
    def test_main_start(self, mock_exit, mock_start):
        sys.argv = ['', 'start']
        main()
        mock_start.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('queue_processors.daemon.Daemon.stop')
    @patch('sys.exit')
    def test_main_stop(self, mock_exit, mock_stop):
        sys.argv = ['', 'stop']
        main()
        mock_stop.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('queue_processors.daemon.Daemon.restart')
    @patch('sys.exit')
    def test_main_restart(self, mock_exit, mock_restart):
        sys.argv = ['', 'restart']
        main()
        mock_restart.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('sys.exit')
    def test_main_invalid(self, mock_exit):
        sys.argv = ['']
        main()
        mock_exit.assert_called_once_with(2)

    @patch('sys.exit',)
    def test_main_unknown(self, mock_exit):
        sys.argv = ['', 'unknown']
        main()
        # Called twice (second time from fall through as exit is mocked)
        # Hence just check that is has been called with an error code of 2
        mock_exit.aasert_has_calls(call(2))
