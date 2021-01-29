# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests the Queue Listener Daemon
"""

import unittest
from unittest import mock

from mock import PropertyMock

import queue_processors.queue_processor.queue_listener_daemon

# pylint: disable=protected-access


class TestQueueListenerDaemon(unittest.TestCase):
    """
    Tests both the class and main method for Queue Listener Daemon
    """
    @staticmethod
    @mock.patch("queue_processors.daemon.sys")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.logging")
    def test_main_daemon_start(patched_logging, patched_daemon, patched_sys):
        """
        Test: The main method correctly starts the daemon
        When: Called by the module main method
        """
        type(patched_sys).argv = PropertyMock(return_value=["", "start"])
        daemon_instance = patched_daemon.return_value
        queue_processors.queue_processor.queue_listener_daemon.main()

        patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
        daemon_instance.start.assert_called_once()
        patched_sys.exit.assert_called_once_with(0)
        patched_logging.assert_not_called()

    @staticmethod
    @mock.patch("queue_processors.daemon.sys")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.logging")
    def test_main_daemon_stop(patched_logging, patched_daemon, patched_sys):
        """
        Test: The main method correctly stops
        When: Called by the module main method
        """
        type(patched_sys).argv = PropertyMock(return_value=["", "stop"])
        daemon_instance = patched_daemon.return_value
        queue_processors.queue_processor.queue_listener_daemon.main()

        patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
        daemon_instance.stop.assert_called_once()
        patched_sys.exit.assert_called_once_with(0)
        patched_logging.assert_not_called()

    @staticmethod
    @mock.patch("queue_processors.daemon.sys")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.logging")
    def test_main_daemon_restart(patched_logging, patched_daemon, patched_sys):
        """
        Test: The main method correctly stops
        When: Called by the module main method
        """
        type(patched_sys).argv = PropertyMock(return_value=["", "restart"])
        daemon_instance = patched_daemon.return_value
        queue_processors.queue_processor.queue_listener_daemon.main()

        patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
        daemon_instance.restart.assert_called_once()
        patched_sys.exit.assert_called_once_with(0)
        patched_logging.assert_not_called()


if __name__ == '__main__':
    unittest.main()
