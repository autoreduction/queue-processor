# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for post process admin and helper functionality
"""

import json
import sys
import unittest

from mock import patch, call, Mock

from model.message.message import Message
from queue_processors.autoreduction_processor.post_process_admin import (PostProcessAdmin, main)
from utils.clients.settings.client_settings_factory import ActiveMQSettings
from utils.settings import ACTIVEMQ_SETTINGS


# pylint:disable=too-many-public-methods, protected-access,no-self-use,too-many-instance-attributes
class TestPostProcessAdmin(unittest.TestCase):
    """Unit tests for Post Process Admin"""
    DIR = "queue_processors.autoreduction_processor"

    def setUp(self):
        """Setup values for Post-Process Admin"""
        self.data = {'data': '\\\\isis\\inst$\\data.nxs',
                     'facility': 'ISIS',
                     'instrument': 'GEM',
                     'rb_number': '1234',
                     'run_number': '4321',
                     'reduction_script': 'print(\'hello\')',
                     'reduction_arguments': 'None'}

        self.message = Message()
        self.message.populate(self.data)

    def test_init(self):
        """
        Test: init parameters are as expected
        When: called with expected arguments
        """
        ppa = PostProcessAdmin(self.message, None)
        self.assertEqual(ppa.message, self.message)
        self.assertEqual(ppa.client, None)
        self.assertIsNotNone(ppa.admin_log_stream)
        self.assertEqual(ppa.data_file, '/isis/data.nxs')
        self.assertEqual(ppa.facility, 'ISIS')
        self.assertEqual(ppa.instrument, 'GEM')
        self.assertEqual(ppa.proposal, '1234')
        self.assertEqual(ppa.run_number, '4321')
        self.assertEqual(ppa.reduction_script, 'print(\'hello\')')
        self.assertEqual(ppa.reduction_arguments, 'None')

    def test_replace_variables(self):
        """Test replacement of variables"""
        print("Should be Unit tested")

    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    @patch(DIR + '.autoreduction_logging_setup.logger.debug')
    def test_send_reduction_message_(self, mock_log_debug, mock_log_info):
        """
        Test: reduction status message has been sent and logged
        When: called within reduce method
        """
        amq_messages = [attr for attr in dir(ActiveMQSettings)
                        if not callable(getattr(ActiveMQSettings, attr))
                        and attr.startswith("reduction")]
        amq_client_mock = Mock()
        ppa = PostProcessAdmin(self.message, amq_client_mock)

        for message in amq_messages:
            amq_message = getattr(ACTIVEMQ_SETTINGS, message)
            ppa.send_reduction_message(message="status",
                                       amq_message=amq_message)

            mock_log_debug.assert_called_with("Calling: %s\n%s",
                                              amq_message,
                                              self.message.serialize(limit_reduction_script=True))
            amq_client_mock.send.assert_called_with(amq_message, ppa.message)

        self.assertEqual(len(amq_messages), amq_client_mock.send.call_count)
        mock_log_info.assert_called_with("Reduction: %s", 'status')

    @patch(DIR + '.autoreduction_logging_setup.logger.debug')
    def test_send_reduction_message_exception(self, mock_log_debug):
        """
        Test: reduction status message has been sent and logged
        When: called within reduce method
        """
        amq_client_mock = Mock()
        amq_client_mock.send.return_value = Exception
        amq_message = "invalid"

        ppa = PostProcessAdmin(self.message, amq_message)

        ppa.send_reduction_message(message="status", amq_message=amq_message)

        mock_log_debug.assert_called_with("Failed to find send reduction message: %s", amq_message)

    @patch(f"{DIR}.post_process_admin.PostProcessAdmin.send_reduction_message")
    def test_determine_reduction_status_problem(self, mock_srm):
        """
        Test: check the correct reduction message is used
        When: when calling send_reduction_message() for each failed use case
        """

        messages = [("Skipped",
                     "Run has been skipped in script",
                     ACTIVEMQ_SETTINGS.reduction_skipped),
                    ("Error",
                     "Permission error: ",
                     ACTIVEMQ_SETTINGS.reduction_error)]
        # message_status = ["skipped", "error"]
        amq_client_mock = Mock()
        for message in messages:
            self.message.message = message[1]
            ppa = PostProcessAdmin(self.message, amq_client_mock)
            ppa.determine_reduction_status()
            mock_srm.assert_called_with(message=message[0],
                                        amq_message=message[2])

    @patch(f"{DIR}.post_process_admin.PostProcessAdmin.send_reduction_message")
    def test_determine_reduction_status_complete(self, mock_srm):
        """
        Test: check the correct reduction message is used
        When: when calling send_reduction_message() with complete status
        """

        # message_status = ["skipped", "error"]
        amq_client_mock = Mock()
        self.message.message = None

        ppa = PostProcessAdmin(self.message, amq_client_mock)
        ppa.determine_reduction_status()
        mock_srm.assert_called_with(message="Complete",
                                    amq_message=ACTIVEMQ_SETTINGS.reduction_complete)

    @patch('logging.Logger.info')
    @patch(f"{DIR}.post_process_admin.PostProcessAdmin.send_reduction_message")
    def test_determine_reduction_status_exception(self, mock_srm, mock_log):
        """
        Test: Assert correct number of logs are performed when
        When: exception triggered by send_reduction_message
        """

        amq_client_mock = Mock()
        self.message.message = False
        mock_srm.return_value = Exception("invalid")

        ppa = PostProcessAdmin(self.message, amq_client_mock)
        ppa.determine_reduction_status()

        self.assertEqual(mock_log.call_count, 2)

    @patch(DIR + '.post_process_admin_utilities.windows_to_linux_path', return_value='path')
    @patch(DIR + '.post_process_admin.PostProcessAdmin.reduce')
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    def test_main(self, mock_init, mock_connect, mock_reduce, _):
        """
        Test: A QueueClient is initialised and connected and ppa.reduce is called
        When: The main method is called
        """
        sys.argv = ['', '/queue/ReductionPending', json.dumps(self.data)]
        main()
        mock_init.assert_called_once()
        mock_connect.assert_called_once()
        mock_reduce.assert_called_once()

    # pylint: disable = too-many-arguments
    @patch('model.message.message.Message.serialize', return_value='test')
    @patch('sys.exit')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    @patch(DIR + '.post_process_admin.PostProcessAdmin.__init__', return_value=None)
    @patch('utils.clients.queue_client.QueueClient.send')
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    def test_main_inner_value_error(self, mock_client_init, mock_connect, mock_send, mock_ppa_init,
                                    mock_logger, mock_exit, _):
        """
        Test: The correct message is sent from the exception handlers in main
        When: A ValueError exception is raised from ppa.reduce
        """

        def raise_value_error(arg1, _):
            """Raise Value Error"""
            self.assertEqual(arg1, self.message)
            raise ValueError('error-message')

        mock_ppa_init.side_effect = raise_value_error
        sys.argv = ['', '/queue/ReductionPending', json.dumps(self.data)]
        main()
        mock_connect.assert_called_once()
        mock_client_init.assert_called_once()
        mock_logger.assert_has_calls([call('Message data error: %s', 'test')])
        mock_exit.assert_called_once()
        self.message.message = 'error-message'
        mock_send.assert_called_once_with(ACTIVEMQ_SETTINGS.reduction_error,
                                          self.message)

    # pylint: disable = too-many-arguments
    @patch('sys.exit')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    @patch(DIR + '.post_process_admin.PostProcessAdmin.__init__', return_value=None)
    @patch('utils.clients.queue_client.QueueClient.send')
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    def test_main_inner_exception(self, mock_client_init, mock_connect, mock_send, mock_ppa_init,
                                  mock_logger, mock_exit):
        """
        Test: The correct message is sent from the exception handlers in main
        When: A bare Exception is raised from ppa.reduce
        """

        def raise_exception(arg1, _):
            """Raise Exception"""
            self.assertEqual(arg1, self.message)
            raise Exception('error-message')

        mock_ppa_init.side_effect = raise_exception
        sys.argv = ['', '/queue/ReductionPending', json.dumps(self.data)]
        main()
        mock_connect.assert_called_once()
        mock_client_init.assert_called_once()
        mock_logger.assert_has_calls([call('PostProcessAdmin error: %s', 'error-message')])
        mock_exit.assert_called_once()
        mock_send.assert_called_once_with(ACTIVEMQ_SETTINGS.reduction_error,
                                          self.message)

    @patch(DIR + '.post_process_admin.PostProcessAdmin.__init__', return_value=None)
    def test_validate_input_success(self, _):
        """
        Test: The attribute value is returned
        When: validate_input is called with an attribute which is not None
        """
        mock_self = Mock()
        mock_self.message = self.message

        actual = PostProcessAdmin.validate_input(mock_self, 'facility')
        self.assertEqual(actual, self.message.facility)

    @patch(DIR + '.post_process_admin.PostProcessAdmin.__init__', return_value=None)
    def test_validate_input_failure(self, _):
        """
        Test: A ValueError is raised
        When: validate_input is called with an attribute who's value is None
        """
        mock_self = Mock()
        mock_self.message = self.message
        mock_self.message.facility = None

        with self.assertRaises(ValueError):
            PostProcessAdmin.validate_input(mock_self, 'facility')
