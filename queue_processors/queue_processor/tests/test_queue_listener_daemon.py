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

from queue_processors.queue_processor.queue_listener_daemon import QueueListenerDaemon
import queue_processors.queue_processor.queue_listener_daemon
from utils.clients.queue_client import QueueClient

# pylint: disable=protected-access


class TestQueueListenerDaemon(unittest.TestCase):
    """
    Tests both the class and main method for Queue Listener Daemon
    """
    @staticmethod
    @mock.patch("queue_processors.daemon.sys")
    @mock.patch("queue_processors.queue_processor." "queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.logging")
    def test_main_daemon_start(patched_logging, patched_daemon, patched_sys):
        """
        Test: The main method correctly starts the daemon
        When: Called by the module main method
        """
        type(patched_sys).argv = PropertyMock(return_value=["", "start"])
        daemon_instance = patched_daemon.return_value
        daemon_instance.safe_shutdown.wait.return_value = True
        queue_processors.queue_processor.queue_listener_daemon.main()

        patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
        daemon_instance.start.assert_called_once()
        patched_sys.exit.assert_called_once_with(0)
        patched_logging.assert_not_called()

    @staticmethod
    @mock.patch("queue_processors.daemon.sys")
    @mock.patch("queue_processors.queue_processor." "queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.logging")
    def test_main_daemon_stop(patched_logging, patched_daemon, patched_sys):
        """
        Test: The main method correctly stops
        When: Called by the module main method
        """
        type(patched_sys).argv = PropertyMock(return_value=["", "stop"])
        daemon_instance = patched_daemon.return_value
        daemon_instance.safe_shutdown.wait.return_value = True
        queue_processors.queue_processor.queue_listener_daemon.main()

        patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
        daemon_instance.stop.assert_called_once()
        daemon_instance.safe_shutdown.wait.assert_called_once_with(timeout=60)
        patched_sys.exit.assert_called_once_with(0)
        patched_logging.assert_not_called()

    @staticmethod
    @mock.patch("queue_processors.daemon.sys")
    @mock.patch("queue_processors.queue_processor." "queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.logging")
    def test_main_daemon_stop_unsafe_shutdown_logs(patched_logging, patched_daemon, patched_sys):
        """
        Test: Main will correctly log a timeout as an error
        When: Trying to shutdown the client after timer fires
        """
        type(patched_sys).argv = PropertyMock(return_value=["", "stop"])
        daemon_instance = patched_daemon.return_value
        daemon_instance.safe_shutdown.wait.return_value = False
        queue_processors.queue_processor.queue_listener_daemon.main()

        patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
        daemon_instance.stop.assert_called_once()
        daemon_instance.safe_shutdown.wait.assert_called_once_with(timeout=60)
        patched_sys.exit.assert_called_once_with(0)

        patched_logging.getLogger.assert_called_once()
        mock_log = patched_logging.getLogger.return_value
        mock_log.error.assert_called_once()

    @staticmethod
    @mock.patch("queue_processors.daemon.sys")
    @mock.patch("queue_processors.queue_processor." "queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("queue_processors.queue_processor.queue_listener_daemon.logging")
    def test_main_daemon_restart(patched_logging, patched_daemon, patched_sys):
        """
        Test: The main method correctly stops
        When: Called by the module main method
        """
        type(patched_sys).argv = PropertyMock(return_value=["", "restart"])
        daemon_instance = patched_daemon.return_value
        daemon_instance.safe_shutdown.wait.return_value = True
        queue_processors.queue_processor.queue_listener_daemon.main()

        patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
        daemon_instance.restart.assert_called_once()
        patched_sys.exit.assert_called_once_with(0)
        patched_logging.assert_not_called()

    def setUp(self):
        self.instance = QueueListenerDaemon(pidfile="/should/never/be/created")

    @mock.patch("queue_processors.queue_processor." "queue_listener_daemon.queue_listener")
    @mock.patch("threading.Timer")
    def test_run(self, patched_timer, patched_processor):
        """
        Test: Run method sets up the stop timer and the main worker thread
        When: When someone calls run() on the daemon class
        """
        self.instance.run()

        patched_processor.main.assert_called_once()
        patched_timer.assert_called_once_with(mock.ANY, self.instance.stop)
        self.assertEqual(self.instance._client_handle, patched_processor.main.return_value)

    @mock.patch("queue_processors.daemon.Daemon.stop")
    def test_stop(self, super_class_stop):
        """
        Test: The stop method correctly shuts down the listener and then
              marks the thread as safely stopped
        When: The daemon is shutting down, typically after the timer fires
        """
        mocked_client = mock.Mock(spec=QueueClient)
        mocked_event = mock.Mock()
        self.instance._client_handle = mocked_client

        self.instance.stop()

        mocked_client.disconnect.assert_called_once()
        super_class_stop.assert_called_once()
        mocked_event.set.assert_called_once()


if __name__ == '__main__':
    unittest.main()
