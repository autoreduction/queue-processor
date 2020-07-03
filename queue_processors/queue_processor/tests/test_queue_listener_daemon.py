# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests the Queue Listener Daemon
"""

import unittest
from unittest import mock

from queue_processors.queue_processor.queue_listener_daemon import \
    QueueListenerDaemon
import queue_processors.queue_processor.queue_listener_daemon
from utils.clients.queue_client import QueueClient

# pylint: disable=protected-access


class TestQueueListenerDaemon(unittest.TestCase):
    """
    Tests both the class and main method for Queue Listener Daemon
    """
    @staticmethod
    @mock.patch("queue_processors.queue_processor."
                "queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("queue_processors.queue_processor."
                "queue_listener_daemon.control_daemon_from_cli")
    @mock.patch("logging.error")
    def test_main(patched_logging, patched_cli, patched_daemon):
        """
        Tests the main method correctly starts and handles the nominal case
        """
        daemon_instance = patched_daemon.return_value
        daemon_instance.safe_shutdown.wait.return_value = True
        queue_processors.queue_processor.queue_listener_daemon.main()

        patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
        patched_cli.assert_called_once_with(patched_daemon.return_value)
        daemon_instance.safe_shutdown.wait.assert_called()
        patched_logging.assert_not_called()

    @staticmethod
    @mock.patch("queue_processors.queue_processor."
                "queue_listener_daemon.QueueListenerDaemon")
    @mock.patch("logging.error")
    def test_main_timeout_logs(patched_logging, patched_daemon):
        """
        Tests main will correctly log a timeout as an error
        """
        daemon_event = patched_daemon.return_value.safe_shutdown
        daemon_event.wait.return_value = False  # i.e. unsafe shutdown
        with mock.patch("queue_processors.queue_processor."
                        "queue_listener_daemon.control_daemon_from_cli"):
            queue_processors.queue_processor.queue_listener_daemon.main()

        patched_logging.assert_called()

    def setUp(self):
        self.instance = QueueListenerDaemon(pidfile="/should/never/be/created")

    @mock.patch("queue_processors.queue_processor."
                "queue_listener_daemon.queue_listener")
    @mock.patch("threading.Timer")
    def test_run(self, patched_timer, patched_processor):
        """
        Tests that run method sets up the stop timer and the main worker thread
        """
        self.instance.run()

        patched_processor.main.assert_called_once()
        patched_timer.assert_called_once_with(mock.ANY, self.instance.stop)
        self.assertEqual(self.instance._client_handle,
                         patched_processor.main.return_value)

    @mock.patch("queue_processors.daemon.Daemon.stop")
    def test_stop(self, super_class_stop):
        """
        Tests the stop method correctly shuts down the listener and then
        marks the thread as safely stopped
        """
        mocked_client = mock.Mock(spec=QueueClient)
        mocked_event = mock.Mock()
        self.instance._client_handle = mocked_client
        self.instance.safe_shutdown = mocked_event

        self.instance.stop()

        mocked_client.disconnect.assert_called_once()
        super_class_stop.assert_called_once()
        mocked_event.set.assert_called_once()

    def test_timer_fires_stop(self):
        """
        Tests the timer correctly calls stop (without testing stop)
        when a given time elapses
        """
        self.instance.stop = mock.Mock()

        # Ensure that timer will fire after a delay
        test_time = 1  # second
        self.instance.stop_interval = test_time
        with mock.patch("queue_processors.queue_processor."
                        "queue_listener_daemon.queue_listener"):
            self.instance.run()

        # Now wait for the timer to fire
        self.instance.stop.assert_not_called()
        self.instance._stop_timer.join()  # Wait for thread to fire
        self.instance.stop.assert_called_once()


if __name__ == '__main__':
    unittest.main()
