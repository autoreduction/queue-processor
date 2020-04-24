# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import json
import unittest

from mock import patch

from queue_processors.queue_processor.queueproc_utils.messaging_utils import MessagingUtils


class TestMessagingUtils(unittest.TestCase):
    """
    Exercises the Messaging Utils functions
    """
    def setUp(self):
        self.valid_arg = "data_dict"
        self.pending_queue_name = '/queue/ReductionPending'

    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.send')
    @patch('utils.clients.queue_client.QueueClient.disconnect')
    def test_send_pending_msg(self, mock_disconnect, mock_send, mock_connect, mock_client):

        MessagingUtils._send_pending_msg(self.valid_arg)

        mock_client.assert_called_once()
        mock_connect.assert_called_once()
        mock_send.assert_called_once()
        (args, kwargs) = mock_send.call_args
        self.assertEqual(args[0], self.pending_queue_name)
        self.assertEqual(args[1], json.dumps(self.valid_arg))
        self.assertEqual(kwargs["priority"], '0')
        self.assertEqual(kwargs["delay"], None)

        mock_disconnect.assert_called_once()
