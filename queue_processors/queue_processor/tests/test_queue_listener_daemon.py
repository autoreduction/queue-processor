# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests the Queue Listener Daemon
"""
from unittest import main, mock
import pytest

from queue_processors.queue_processor import queue_listener_daemon

from queue_processors.queue_processor.queue_listener_daemon import QueueListenerDaemon


@mock.patch("queue_processors.queue_processor.queue_listener_daemon.queue_listener")
def test_daemon_start(patched_queue_listener):
    """
    Test: The main method correctly starts the daemon
    """
    mock_client, mock_listener = mock.Mock(), mock.Mock()
    patched_queue_listener.main.return_value = (mock_client, mock_listener)
    qld = QueueListenerDaemon("/tmp/file.pid")
    qld.logger = mock.Mock()
    # avoids blocking the test in the while sleep loop
    qld._shutting_down = True  # pylint:disable=protected-access
    qld.run()

    mock_client.disconnect.assert_not_called()
    mock_listener.is_processing_message.assert_not_called()

    patched_queue_listener.main.assert_called_once()
    qld.logger.info.assert_called_once()


@mock.patch("queue_processors.queue_processor.queue_listener_daemon.time")
@mock.patch("queue_processors.queue_processor.queue_listener_daemon.queue_listener")
def test_daemon_start_goes_into_while_loop(patched_queue_listener, time: mock.Mock):
    """
    Test: The main method correctly starts the daemon
    """
    mock_client, mock_listener = mock.Mock(), mock.Mock()
    patched_queue_listener.main.return_value = (mock_client, mock_listener)

    qld = QueueListenerDaemon("/tmp/file.pid")
    qld.logger = mock.Mock()

    def start_shutting_down(_):
        qld._shutting_down = True  # pylint:disable=protected-access

    # avoid getting stuck into infinite while loop by adding a side effect to the
    # mock call - which sets the Daemon into shutting down mode so that it breaks the loop
    time.sleep.side_effect = start_shutting_down
    # avoids blocking the test in the while sleep loop
    qld.run()
    time.sleep.assert_called_once_with(0.5)

    mock_client.disconnect.assert_not_called()
    mock_listener.is_processing_message.assert_not_called()

    patched_queue_listener.main.assert_called_once()
    qld.logger.info.assert_called_once()


@mock.patch("queue_processors.queue_processor.queue_listener_daemon.queue_listener")
def test_daemon_start_and_stop_while_not_processing(patched_queue_listener):
    """
    Test: The main method correctly stops the daemon when nothing is being processed
    """
    mock_client, mock_listener = mock.Mock(), mock.Mock()
    patched_queue_listener.main.return_value = (mock_client, mock_listener)
    qld = QueueListenerDaemon("/tmp/file.pid")
    # avoids blocking the test in the while sleep loop
    qld._shutting_down = True  # pylint:disable=protected-access
    qld.run()

    qld.logger = mock.Mock()
    mock_listener.is_processing_message.return_value = False
    qld.stop()

    mock_client.disconnect.assert_called_once()
    mock_listener.is_processing_message.assert_called_once()
    qld.logger.info.assert_called_once()


@mock.patch("queue_processors.queue_processor.queue_listener_daemon.queue_listener")
def test_daemon_start_and_stop_while_processing(patched_queue_listener):
    """
    Test: The main method stops the daemon and logs when a run is processing
    """
    mock_client, mock_listener = mock.Mock(), mock.Mock()
    patched_queue_listener.main.return_value = (mock_client, mock_listener)
    qld = QueueListenerDaemon("/tmp/file.pid")
    # avoids blocking the test in the while sleep loop
    qld._shutting_down = True  # pylint:disable=protected-access
    qld.run()

    qld.logger = mock.Mock()
    mock_listener.is_processing_message.return_value = True
    qld.stop()

    mock_client.disconnect.assert_called_once()
    mock_listener.is_processing_message.assert_called_once()
    assert qld.logger.info.call_count == 2


def test_daemon_stop_without_starting():
    """
    Test: The main method stops the daemon and logs when a run is processing
    """
    qld = QueueListenerDaemon("/tmp/file.pid")
    with pytest.raises(RuntimeError):
        qld.stop()


@mock.patch("queue_processors.daemon.sys")
@mock.patch("queue_processors.queue_processor.queue_listener_daemon.QueueListenerDaemon")
@mock.patch("queue_processors.queue_processor.queue_listener_daemon.logging")
def test_main_daemon_start(patched_logging, patched_daemon, patched_sys):
    """
    Test: The main method correctly starts the daemon
    When: Called by the module main method
    """
    type(patched_sys).argv = mock.PropertyMock(return_value=["", "start"])
    daemon_instance = patched_daemon.return_value
    queue_listener_daemon.main()

    patched_daemon.assert_called_once_with("/tmp/QueueListenerDaemon.pid")
    daemon_instance.start.assert_called_once()
    patched_sys.exit.assert_called_once_with(0)
    patched_logging.assert_not_called()


if __name__ == '__main__':
    main()
