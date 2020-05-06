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
    Exercises the Queue Processor
    """
    def setUp(self):
        self.test_consumer_name = "Test_Autoreduction_QueueProcessor"
        self.rb_number = -1
        self.reason = "test"
        # self.logger = MagicMock()

    @patch('logging.Logger.info')
    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.subscribe_autoreduce')
    def test_setup_connection(self, mock_sub_ar, mock_connect, mock_client, mock_logger_info):
        """
        Test: Connection to ActiveMQ setup, along with subscription to queues
        When: setup_connection is called with a consumer name
        """
        queue_processor.setup_connection(self.test_consumer_name)

        mock_logger_info.assert_called_once()
        mock_client.assert_called_once()
        mock_connect.assert_called_once()
        mock_sub_ar.assert_called_once()

        (args, _) = mock_sub_ar.call_args
        self.assertEqual(args[0], self.test_consumer_name)
        self.assertIsInstance(args[1], Listener)
        self.assertIsInstance(args[1]._client, QueueClient)

    @patch('logging.Logger.warning')
    def test_construct_and_send_skipped(self, mock_logger_warning):
        """
        Test: _data_dict['message'] is given a value,and the _data_dict is sent via the QueueClient
        When: _construct_and_send_skipped is called
        """
        mock_client = MagicMock(name="QueueClient")
        listener = Listener(mock_client)
        listener._construct_and_send_skipped(self.rb_number, self.reason)

        mock_logger_warning.assert_called_once()

        self.assertIsNotNone(listener._data_dict['message'])
        mock_client.send.assert_called_once_with(ACTIVEMQ_SETTINGS.reduction_skipped,
                                                 Message(listener._data_dict),
                                                 priority=listener._priority)
        message = mock_client.send.call_args[0][1]
        self.assertEqual(message.description, listener._data_dict)
