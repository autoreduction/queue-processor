# ############################################################################### #
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the queue processor
"""

import uuid
from unittest import TestCase, mock
from unittest.mock import patch, MagicMock

from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.clients.queue_client import QueueClient
from autoreduce_utils.message.message import Message

from autoreduce_qp.queue_processor import queue_listener
from autoreduce_qp.queue_processor.handle_message import HandleMessage
from autoreduce_qp.queue_processor.queue_listener import QueueListener


class TestQueueProcessor(TestCase):
    """
    Exercises the functions within listener.py
    """
    @patch("autoreduce_qp.queue_processor.queue_listener.QueueClient.__init__", return_value=None)
    @patch("autoreduce_qp.queue_processor.queue_listener.QueueClient.connect")
    @patch("autoreduce_qp.queue_processor.queue_listener.QueueClient.subscribe")
    def test_setup_connection(self, mock_subscribe, mock_connect, mock_client):  # pylint:disable=no-self-use
        """
        Test: Connection to ActiveMQ setup, along with subscription to queues
        When: setup_connection is called with a consumer name
        """
        queue_listener.setup_connection()

        mock_subscribe.assert_called_once()
        mock_client.assert_called_once()
        mock_connect.assert_called_once()


class TestQueueListener(TestCase):
    """
    Exercises the Listener
    """
    def setUp(self):
        self.mocked_client = mock.Mock(spec=QueueClient)
        self.mocked_handler = mock.MagicMock(spec=HandleMessage)
        self.frame = self._get_frame()

        with patch("autoreduce_qp.queue_processor.queue_listener"
                   ".HandleMessage", return_value=self.mocked_handler), \
             patch("logging.getLogger") as patched_logger:
            self.listener = QueueListener(self.mocked_client)
            self.mocked_logger = patched_logger.return_value

    @staticmethod
    def _get_frame():
        class StompFrameMock():
            def __init__(self, headers, body):
                self.headers = headers
                self.body = body

        headers = {
            "destination": "/queue/DataReady",
            "priority": mock.NonCallableMock(),
            "message-id": str(uuid.uuid4()),
            "subscription": str(uuid.uuid4())
        }
        return StompFrameMock(headers=headers, body={"run_number": 1234567})

    def test_on_message_message_unknown_field(self):
        """
        Test receiving a message with an unknown field
        """
        self.frame.body["apples"] = 1234567
        self.listener.on_message(self.frame)
        self.mocked_logger.error.assert_called_once()

    def test_on_message_unknown_topic(self):
        """Test receiving a message on an unknown topic"""
        self.frame.headers["destination"] = "unknown"
        self.listener.on_message(self.frame)
        self.mocked_logger.error.assert_called_once()

    def test_on_message_sends_acknowledgement(self):
        """Test that acknowledgement is sent when the message is received and parsed successfully"""
        self.listener.on_message(self.frame)
        self.assertFalse(self.listener.is_processing_message())
        self.mocked_logger.info.assert_called_once()
        self.mocked_client.ack.assert_called_once_with(self.frame.headers["message-id"],
                                                       self.frame.headers["subscription"])
        self.mocked_handler.data_ready.assert_called_once()
        self.assertIsInstance(self.mocked_handler.data_ready.call_args[0][0], Message)

    def test_on_message_handler_catches_exceptions(self):
        """Test on_message correctly handles an exception being raised"""
        def raise_expected_exception(msg):
            raise Exception(msg)

        self.mocked_handler.data_ready.side_effect = raise_expected_exception
        self.listener.on_message(self.frame)
        self.mocked_logger.error.assert_called_once()

    def test_on_disconnected(self):
        """Test correct calls on disconnect"""
        mock_con = MagicMock()
        mock_sub = MagicMock()
        self.mocked_client.connect = mock_con
        self.mocked_client.subscribe = mock_sub

        self.listener.on_disconnected()

        mock_con.assert_called_once()
        mock_sub.assert_called_once()

    @patch("autoreduce_qp.queue_processor.queue_listener.time.sleep")
    def test_on_diconnected_fail_to_reconnect_retries(self, mock_sleep):
        """
        Test: Attempts to reconnect
        When: Reconnect fails
        """
        mock_con = MagicMock()
        mock_sub = MagicMock()
        self.mocked_client.connect = mock_con
        self.mocked_client.subscribe = mock_sub
        mock_con.side_effect = [ConnectionException("AMQ"), None]

        self.listener.on_disconnected()

        mock_con.assert_called()
        mock_sleep.assert_called()
        mock_con.assert_called()
        mock_sub.assert_called_once()
