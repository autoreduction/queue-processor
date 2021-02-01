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
import tempfile
from mock import patch, call, Mock

from model.message.message import Message
from queue_processors.queue_processor.reduction_runner.reduction_runner import ReductionRunner, main


class TestReductionRunner(unittest.TestCase):
    """Unit tests for Post Process Admin"""
    DIR = "queue_processors.queue_processor.reduction_runner"

    def setUp(self):
        """Setup values for Post-Process Admin"""
        self.data = {
            'data': '\\\\isis\\inst$\\data.nxs',
            'facility': 'ISIS',
            'instrument': 'GEM',
            'rb_number': '1234',
            'run_number': '4321',
            'reduction_script': 'print(\'hello\')',  # not actually used for the reduction
            'reduction_arguments': 'None'
        }

        self.message = Message()
        self.message.populate(self.data)

    def test_init(self):
        """
        Test: init parameters are as expected
        When: called with expected arguments
        """
        runner = ReductionRunner(self.message)
        self.assertEqual(runner.message, self.message)
        self.assertIsNotNone(runner.admin_log_stream)
        self.assertEqual(runner.data_file, '/isis/data.nxs')
        self.assertEqual(runner.facility, 'ISIS')
        self.assertEqual(runner.instrument, 'GEM')
        self.assertEqual(runner.proposal, '1234')
        self.assertEqual(runner.run_number, '4321')
        self.assertEqual(runner.reduction_arguments, 'None')

    @patch(f'{DIR}.utilities.windows_to_linux_path', return_value='path')
    @patch(f'{DIR}.reduction_runner.ReductionRunner.reduce')
    def test_main(self, mock_reduce, _):
        """
        Test: A QueueClient is initialised and connected and ppa.reduce is called
        When: The main method is called
        """
        with tempfile.NamedTemporaryFile() as tmp_file:
            sys.argv = ['', json.dumps(self.data), tmp_file.name]
            main()
            out_data = json.loads(tmp_file.read())
        mock_reduce.assert_called_once()
        assert self.data["facility"] == out_data["facility"]
        assert self.data["run_number"] == out_data["run_number"]
        assert self.data["instrument"] == out_data["instrument"]
        assert self.data["rb_number"] == out_data["rb_number"]
        assert self.data["data"] == out_data["data"]
        assert self.data["reduction_script"] == out_data["reduction_script"]
        assert self.data["reduction_arguments"] == out_data["reduction_arguments"]

    @patch(f'{DIR}.reduction_runner.logger.info')
    @patch(f'{DIR}.reduction_runner.ReductionRunner.__init__')
    def test_main_inner_value_error(self, mock_runner_init, mock_logger_info):
        """
        Test: The correct message is sent from the exception handlers in main
        When: A ValueError exception is raised from ppa.reduce
        """
        expected_error_msg = 'error-message'

        def raise_value_error(arg1):
            """Raise Value Error"""
            self.assertEqual(arg1, self.message)
            raise ValueError(expected_error_msg)

        mock_runner_init.side_effect = raise_value_error
        with tempfile.NamedTemporaryFile() as tmp_file:
            sys.argv = ['', json.dumps(self.data), tmp_file.name]
            self.assertRaises(ValueError, main)

        self.message.message = expected_error_msg
        mock_logger_info.assert_has_calls(
            [call('Message data error: %s', self.message.serialize(limit_reduction_script=True))])

    # pylint: disable = too-many-arguments
    @patch(f'{DIR}.reduction_runner.logger.info')
    @patch(f'{DIR}.reduction_runner.ReductionRunner.__init__')
    def test_main_inner_exception(self, mock_runner_init, mock_logger_info):
        """
        Test: The correct message is sent from the exception handlers in main
        When: A bare Exception is raised from ppa.reduce
        """
        def raise_exception(arg1):
            """Raise Exception"""
            self.assertEqual(arg1, self.message)
            raise Exception('error-message')

        mock_runner_init.side_effect = raise_exception
        with tempfile.NamedTemporaryFile() as tmp_file:
            sys.argv = ['', json.dumps(self.data), tmp_file.name]
            self.assertRaises(Exception, main)
        mock_logger_info.assert_has_calls([call('ReductionRunner error: %s', 'error-message')])

    @patch(f'{DIR}.reduction_runner.ReductionRunner.__init__', return_value=None)
    def test_validate_input_success(self, _):
        """
        Test: The attribute value is returned
        When: validate_input is called with an attribute which is not None
        """
        mock_self = Mock()
        mock_self.message = self.message

        actual = ReductionRunner.validate_input(mock_self, 'facility')
        self.assertEqual(actual, self.message.facility)

    @patch(f'{DIR}.reduction_runner.ReductionRunner.__init__', return_value=None)
    def test_validate_input_failure(self, _):
        """
        Test: A ValueError is raised
        When: validate_input is called with an attribute who's value is None
        """
        mock_self = Mock()
        mock_self.message = self.message
        mock_self.message.facility = None

        with self.assertRaises(ValueError):
            ReductionRunner.validate_input(mock_self, 'facility')
