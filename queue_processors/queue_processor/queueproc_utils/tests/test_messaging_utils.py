# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the messaging utils
"""
import json
import unittest

from mock import patch

from queue_processors.queue_processor.queueproc_utils.messaging_utils import MessagingUtils


class TestMessagingUtils(unittest.TestCase):
    # pylint:disable=protected-access
    """
    Exercises the Messaging Utils functions
    """
    def setUp(self):
        self.test_data = "data_dict"
        self.pending_queue_name = '/queue/ReductionPending'

    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.send')
    @patch('utils.clients.queue_client.QueueClient.disconnect')
    def test_send_pending_msg(self, mock_disconnect, mock_send, mock_connect, mock_client):
        """
        Test: A QueueClient is connected to, used to send the given argument
        to the pending-queue, and finally disconnected from
        When: _send_pending_msg is called with a data argument
        """
        MessagingUtils._send_pending_msg(self.test_data)

        mock_client.assert_called_once()
        mock_connect.assert_called_once()
        mock_send.assert_called_once()
        mock_disconnect.assert_called_once()

        (args, kwargs) = mock_send.call_args
        self.assertEqual(args[0], self.pending_queue_name)
        self.assertEqual(args[1], self.test_data)
        self.assertEqual(kwargs["priority"], '0')
        self.assertEqual(kwargs["delay"], None)
