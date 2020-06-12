# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the messaging utils
"""
import unittest

from mock import patch, Mock

from message.job import Message
from queue_processors.queue_processor.queueproc_utils.messaging_utils import MessagingUtils
from queue_processors.queue_processor.settings import FACILITY

UTILS_PATH = 'queue_processors.queue_processor.queueproc_utils'
MESSAGE_CLASS_PATH = UTILS_PATH + '.messaging_utils.MessagingUtils'


class TestMessagingUtils(unittest.TestCase):
    # pylint:disable=protected-access
    """
    Exercises the Messaging Utils functions
    """

    def setUp(self):
        # Test values
        self.run_number = 123
        self.instrument_name = 'GEM'
        self.rb_number = '456'
        self.version = 1

        mock_run = Mock()
        mock_run.run_number = self.run_number
        mock_run.instrument.name = self.instrument_name
        mock_run.experiment.reference_number = self.rb_number
        mock_run.run_version = self.version
        self.mock_run = mock_run

    # pylint:disable=no-self-use
    @patch(f'{MESSAGE_CLASS_PATH}._make_pending_msg')
    @patch(f'{MESSAGE_CLASS_PATH}._send_pending_msg')
    def test_send_pending(self, mock_send_pending, mock_make_pending):
        """
        Test: The correct control functions are called and the variables feed through as expected
        When: Calling the control function send_pending
        """
        mock_make_pending.return_value = 'test'
        MessagingUtils().send_pending('123')
        mock_make_pending.assert_called_once_with('123')
        mock_send_pending.assert_called_once_with('test', None)

    @patch(f'{MESSAGE_CLASS_PATH}._make_pending_msg')
    @patch(f'{MESSAGE_CLASS_PATH}._send_pending_msg')
    def test_send_cancel(self, mock_send_pending, mock_make_pending):
        """
        Test: The correct control functions are called and the variables feed through as expected
        When: Calling the control function cancel_pending
        """
        mock_msg = Mock()
        mock_make_pending.return_value = mock_msg
        MessagingUtils().send_cancel('123')
        mock_make_pending.assert_called_once_with('123')
        mock_send_pending.assert_called_once_with(mock_msg)
        self.assertEqual(mock_msg.cancel, True)

    @patch('model.database.access.start_database')
    @patch(f'{UTILS_PATH}.reduction_run_utils.ReductionRunUtils.get_script_and_arguments')
    def test_make_pending_msg(self, mock_get_scr_and_args, mock_start_db):
        """
        Test: A Message with expected value is generated
        When: Calling the make_pending_msg
        """
        file_path = 'file/path'
        script = 'script'
        args = {'arg': 1}
        # Setup Mock values
        mock_get_scr_and_args.return_value = (script, args)

        db_conn = Mock()
        query_set = Mock()
        mock_record = Mock()
        mock_record.file_path = file_path
        query_set.first.return_value = mock_record
        db_conn.data_model.DataLocation.filter_by.return_value = query_set
        mock_start_db.return_value = db_conn

        actual = MessagingUtils()._make_pending_msg(self.mock_run)
        self.assertIsInstance(actual, Message)
        self.assertEqual(actual.run_number, self.run_number)
        self.assertEqual(actual.instrument, self.instrument_name)
        self.assertEqual(actual.rb_number, self.rb_number)
        self.assertEqual(actual.data, file_path)
        self.assertEqual(actual.reduction_script, script)
        self.assertEqual(actual.reduction_arguments, args)
        self.assertEqual(actual.run_version, self.version)
        self.assertEqual(actual.facility, FACILITY)

    @patch(f'{UTILS_PATH}.reduction_run_utils.ReductionRunUtils.get_script_and_arguments')
    @patch('model.database.access.start_database')
    def test_make_pending_msg_exception(self, mock_start_db, mock_get_script):
        """
        Test: An exception is raised
        When: Calling the make_pending_msg and unable to find DataLocation
        """
        mock_get_script.return_value = (1, 2)
        db_conn = Mock()
        query_set = Mock()
        query_set.first.return_value = None
        db_conn.data_model.DataLocation.filter_by.return_value = query_set
        mock_start_db.return_value = db_conn

        self.assertRaises(RuntimeError, MessagingUtils()._make_pending_msg, self.mock_run)

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
        test_data = "data_dict"
        pending_queue_name = '/queue/ReductionPending'
        MessagingUtils()._send_pending_msg(test_data)

        mock_client.assert_called_once()
        mock_connect.assert_called_once()
        mock_send.assert_called_once()
        mock_disconnect.assert_called_once()

        (args, kwargs) = mock_send.call_args
        self.assertEqual(args[0], pending_queue_name)
        self.assertEqual(args[1], test_data)
        self.assertEqual(kwargs["priority"], '0')
        self.assertEqual(kwargs["delay"], None)
