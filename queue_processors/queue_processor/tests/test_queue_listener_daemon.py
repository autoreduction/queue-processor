# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests the Queue Listener Daemon
"""

import os
import unittest
from unittest import mock

from mock import Mock

from queue_processors.queue_processor.queue_listener_daemon import QueueListenerDaemon


@mock.patch("queue_processors.queue_processor.queue_listener_daemon.queue_listener")
def test_main_daemon_start(patched_queue_listener):
    """
    Test: The main method correctly starts the daemon
    """
    mock_client, mock_listener = mock.Mock(), mock.Mock()
    patched_queue_listener.main.return_value = (mock_client, mock_listener)
    qld = QueueListenerDaemon("/tmp/file.pid")
    qld.logger = Mock()
    # avoids blocking the test in the while sleep loop
    qld._shutting_down = True  # pylint:disable=protected-access
    qld.run()

    mock_client.disconnect.assert_not_called()
    mock_listener.is_processing_message.assert_not_called()

    patched_queue_listener.main.assert_called_once()
    qld.logger.info.assert_called_once()


@mock.patch("queue_processors.queue_processor.queue_listener_daemon.queue_listener")
def test_main_daemon_start_and_stop_while_not_processing(patched_queue_listener):
    """
    Test: The main method correctly stops the daemon when nothing is being processed
    """
    mock_client, mock_listener = mock.Mock(), mock.Mock()
    patched_queue_listener.main.return_value = (mock_client, mock_listener)
    qld = QueueListenerDaemon("/tmp/file.pid")
    # avoids blocking the test in the while sleep loop
    qld._shutting_down = True  # pylint:disable=protected-access
    qld.run()

    qld.logger = Mock()
    mock_listener.is_processing_message.return_value = False
    qld.stop()

    mock_client.disconnect.assert_called_once()
    mock_listener.is_processing_message.assert_called_once()
    qld.logger.info.assert_called_once()


@mock.patch("queue_processors.queue_processor.queue_listener_daemon.queue_listener")
def test_main_daemon_start_and_stop_while_processing(patched_queue_listener):
    """
    Test: The main method stops the daemon and logs when a run is processing
    """
    mock_client, mock_listener = mock.Mock(), mock.Mock()
    patched_queue_listener.main.return_value = (mock_client, mock_listener)
    qld = QueueListenerDaemon("/tmp/file.pid")
    # avoids blocking the test in the while sleep loop
    qld._shutting_down = True  # pylint:disable=protected-access
    qld.run()

    qld.logger = Mock()
    mock_listener.is_processing_message.return_value = True
    qld.stop()

    mock_client.disconnect.assert_called_once()
    mock_listener.is_processing_message.assert_called_once()
    assert qld.logger.info.call_count == 2


if __name__ == '__main__':
    unittest.main()
