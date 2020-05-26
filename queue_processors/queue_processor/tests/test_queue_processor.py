# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the queue processor
"""
import unittest

from mock import patch, MagicMock

from message.job import Message
from queue_processors.queue_processor import queue_processor
from queue_processors.queue_processor.queue_processor import Listener
from utils.clients.queue_client import QueueClient
from utils.settings import ACTIVEMQ_SETTINGS


class TestQueueProcessor(unittest.TestCase):
    # pylint:disable=protected-access
    """
    Exercises the functions within queue_processor.py
    """
    def setUp(self):
        self.test_consumer_name = "Test_Autoreduction_QueueProcessor"

    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.subscribe_autoreduce')
    def test_setup_connection(self, mock_sub_ar, mock_connect, mock_client):
        """
        Test: Connection to ActiveMQ setup, along with subscription to queues
        When: setup_connection is called with a consumer name
        """
        queue_processor.setup_connection(self.test_consumer_name)

        mock_client.assert_called_once()
        mock_connect.assert_called_once()
        mock_sub_ar.assert_called_once()

        (args, _) = mock_sub_ar.call_args
        self.assertEqual(args[0], self.test_consumer_name)
        self.assertIsInstance(args[1], Listener)
        self.assertIsInstance(args[1]._client, QueueClient)


class TestListener(unittest.TestCase):
    """
    Exercises the Listener
    """
    def setUp(self):
        self.test_rb_number = -1
        self.test_reason = "test"

    def test_construct_and_send_skipped(self):
        # pylint:disable=protected-access
        """
        Test: The message is sent via the QueueClient with a populated message attribute
        When: _construct_and_send_skipped is called
        """
        mock_client = MagicMock(name="QueueClient")
        listener = Listener(mock_client)
        listener._construct_and_send_skipped(self.test_rb_number, self.test_reason)

        self.assertIsNotNone(listener.message)
        mock_client.send.assert_called_once_with(ACTIVEMQ_SETTINGS.reduction_skipped,
                                                 listener.message,
                                                 priority=listener._priority)
        sent_message = mock_client.send.call_args[0][1]
        self.assertEqual(sent_message, listener.message)