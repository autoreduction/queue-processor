# ############################################################################### #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint:disable=protected-access
import json
from pathlib import Path
import pathlib
import sys
import unittest
import tempfile
from unittest.mock import create_autospec, mock_open, patch, call, Mock
from autoreduce_utils.message.message import Message
from autoreduce_utils.settings import CYCLE_DIRECTORY

from parameterized import parameterized
import pytest

from autoreduce_qp.queue_processor.reduction.exceptions import ReductionScriptError
from autoreduce_qp.queue_processor.reduction.runner import ReductionRunner, main, write_reduction_message
from autoreduce_qp.queue_processor.reduction.tests.common import add_data_and_message, add_bad_data_and_message


class TestReductionRunner(unittest.TestCase):
    DIR = "autoreduce_qp.queue_processor.reduction"

    def setUp(self) -> None:
        self.data, self.message = add_data_and_message()
        self.bad_data, self.bad_message = add_bad_data_and_message()
        self.run_name = "Test run name"

    def test_init(self):
        """
        Test: init parameters are as expected
        When: called with expected arguments
        """
        runner = ReductionRunner(self.message, self.run_name)
        self.assertEqual(runner.message, self.message)
        self.assertIsNotNone(runner.admin_log_stream)
        self.assertEqual(
            runner.data_file,
            CYCLE_DIRECTORY % ("TESTINSTRUMENT", "21_1") + '/data.nxs',
        )
        self.assertEqual(runner.facility, 'ISIS')
        self.assertEqual(runner.instrument, 'TESTINSTRUMENT')
        self.assertEqual(runner.proposal, '1234')
        self.assertEqual(runner.run_number, '4321')
        self.assertEqual(
            runner.reduction_arguments, {
                "standard_vars": {
                    "arg1": "differentvalue",
                    "arg2": 321
                },
                "advanced_vars": {
                    "adv_arg1": "advancedvalue2",
                    "adv_arg2": ""
                }
            })

    # Create test for write_reduction_message
    def test_main_write_reduction_message(self):
        """
        Test: write_reduction_message is called
        When: called with expected arguments
        """
        with tempfile.NamedTemporaryFile() as tmp_file:
            runner = ReductionRunner(self.message, self.run_name)
            write_reduction_message(runner, self.run_name, tmp_file.name)
            data = json.load(tmp_file)
            assert self.data["facility"] == data["facility"]
            assert self.data["run_number"] == data["run_number"]
            assert self.data["instrument"] == data["instrument"]
            assert self.data["rb_number"] == data["rb_number"]
            assert self.data["data"] == data["data"]
            assert self.data["reduction_script"] == data["reduction_script"]
            assert self.data["reduction_arguments"] == data["reduction_arguments"]

    @patch(f'{DIR}.runner.ReductionRunner.reduce')
    def test_main(self, mock_reduce):
        """
        Test: the reduction is run and on success finishes as expected
        When: The main method is called
        """
        with tempfile.NamedTemporaryFile() as tmp_file:
            sys.argv = ['', json.dumps(self.data), self.run_name, tmp_file.name]
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

    @patch(f'{DIR}.runner.ReductionRunner.reduce', side_effect=Exception)
    def test_main_reduce_raises(self, mock_reduce):
        """
        Test: the reduction is called but the reduce function raises an Exception
        When: The main method is called
        """
        with tempfile.NamedTemporaryFile() as tmp_file:
            sys.argv = ['', json.dumps(self.data), self.run_name, tmp_file.name]
            self.assertRaises(Exception, main)
        mock_reduce.assert_called_once()

    def test_main_bad_data_for_populate(self):
        """
        Test: Providing bad data for the `main` function, i.e. not enough arguments
        """
        with tempfile.NamedTemporaryFile() as tmp_file:
            sys.argv = ['', json.dumps({"apples": 13}), self.run_name, tmp_file.name]
            self.assertRaises(ValueError, main)

    @patch(f'{DIR}.runner.logger.info')
    @patch(f'{DIR}.runner.ReductionRunner.__init__')
    def test_main_inner_exception(self, mock_runner_init, mock_logger_info):
        """
        Test: The correct message is sent from the exception handlers in main
        When: A ValueError exception is raised from ppa.reduce
        """
        expected_error_msg = 'error-message'

        def raise_value_error(message, run_name):
            """Raise Value Error"""
            self.assertEqual(run_name, self.run_name)
            self.assertEqual(message, self.message)
            raise Exception(expected_error_msg)

        mock_runner_init.side_effect = raise_value_error
        with tempfile.NamedTemporaryFile() as tmp_file:
            sys.argv = ['', json.dumps(self.data), self.run_name, tmp_file.name]
            self.assertRaises(Exception, main)

        self.message.message = expected_error_msg
        mock_logger_info.assert_has_calls(
            [call('Message data error: %s', self.message.serialize(limit_reduction_script=True))])

    @patch(f'{DIR}.runner.logger.info')
    @patch(f'{DIR}.runner.ReductionRunner._get_mantid_version', return_value="5.1.0")
    def test_reduce_bad_datafile(self, _get_mantid_version: Mock, mock_logger_info: Mock):
        """
        Test: Bad datafile is provided
        """
        self.bad_message.description = "testdescription"
        runner = ReductionRunner(self.bad_message, self.run_name)
        runner.reduce()
        mock_logger_info.assert_called_once()
        assert mock_logger_info.call_args[0][1] == "testdescription"
        _get_mantid_version.assert_called_once()
        assert runner.message.message, ('Error encountered when trying to access the datafile'
                                        ' /isis/NDXTESTINSTRUMENT/Instrument/data/cycle_21_1/data.nxs')

    @patch(f'{DIR}.runner.ReductionScript', side_effect=PermissionError("error message"))
    def test_reduce_reductionscript_any_raise(self, _: Mock):
        """
        Test: ReductionDirectory raising any exception
        """
        with tempfile.NamedTemporaryFile() as tmpfile:
            self.message.data = tmpfile.name

            runner = ReductionRunner(self.message, self.run_name)
            runner.reduce()

        assert runner.message.message == "Error encountered when trying to read the reduction script"
        assert "Exception:" in runner.message.reduction_log
        assert "error message" in runner.message.reduction_log

    @patch(f'{DIR}.runner.ReductionDirectory', side_effect=PermissionError("error message"))
    def test_reduce_reductiondirectory_any_raise(self, _: Mock):
        """
        Test: ReductionDirectory raising any exception
        """
        with tempfile.NamedTemporaryFile() as tmpfile:
            self.message.data = tmpfile.name

            runner = ReductionRunner(self.message, self.run_name)
            runner.reduce()

        assert runner.message.message == "Error encountered when trying to read the reduction directory"
        assert "Exception:" in runner.message.reduction_log
        assert "error message" in runner.message.reduction_log

    @patch(f'{DIR}.runner.ReductionRunner._get_mantid_version', return_value="5.1.0")
    @patch(f'{DIR}.runner.reduce')
    def test_reduce_throws_reductionscripterror(self, reduce: Mock, _get_mantid_version: Mock):
        """
        Test: reduce throwing an ReductionScriptError
        """
        reduce.side_effect = ReductionScriptError
        with tempfile.NamedTemporaryFile() as tmpfile:
            self.message.data = tmpfile.name

            runner = ReductionRunner(self.message, self.run_name)
            runner.reduce()

        reduce.assert_called_once()
        _get_mantid_version.assert_called_once()
        assert str(reduce.call_args[0][2][0].path) == tmpfile.name
        assert runner.message.reduction_data is None
        assert runner.message.software == "5.1.0"
        assert "Error encountered when running the reduction script" in runner.message.message

    @patch(f'{DIR}.runner.ReductionRunner._get_mantid_version', return_value="5.1.0")
    @patch(f'{DIR}.runner.reduce')
    def test_reduce_throws_any_exception(self, reduce: Mock, _get_mantid_version: Mock):
        """
        Test: Reduce throwing any exception
        """
        reduce.side_effect = Exception
        with tempfile.NamedTemporaryFile() as tmpfile:
            self.message.data = tmpfile.name

            runner = ReductionRunner(self.message, self.run_name)
            runner.reduce()

        reduce.assert_called_once()
        _get_mantid_version.assert_called_once()
        assert str(reduce.call_args[0][2][0].path) == tmpfile.name
        assert runner.message.reduction_data is None
        assert runner.message.software == "5.1.0"
        assert "REDUCTION Error:" in runner.message.message

    @parameterized.expand([["str"], ["list"]])
    @patch(f'{DIR}.runner.ReductionRunner._get_mantid_version', return_value="5.1.0")
    @patch(f'{DIR}.runner.reduce')
    def test_reduce_ok(self, datafile_type: str, reduce: Mock, _get_mantid_version: Mock):
        """
        Test: An OK reduction
        """
        with tempfile.NamedTemporaryFile() as tmpfile:
            if datafile_type == "str":
                self.message.data = tmpfile.name
            else:
                self.message.data = [tmpfile.name, tmpfile.name]

            runner = ReductionRunner(self.message, self.run_name)
            runner.reduce()

        reduce.assert_called_once()
        _get_mantid_version.assert_called_once()
        assert str(reduce.call_args[0][2][0].path) == tmpfile.name
        assert runner.message.reduction_data is not None
        assert runner.message.reduction_log is not None
        assert runner.message.message is None
        assert runner.message.software == "5.1.0"

    @staticmethod
    @patch(f'{DIR}.runner.logger')
    def test_get_mantid_version(logger: Mock):
        """
        Test: Getting the mantid version
        """
        pytest.importorskip(modname="mantid", minversion="6.2.0", reason="Mantid not installed")
        assert ReductionRunner._get_mantid_version() is not None

    @patch(f'{DIR}.runner.ReductionRunner._get_mantid_version', return_value="5.1.0")
    @patch(f'{DIR}.runner.reduce')
    def test_flat_output_respected(self, reduce: Mock, _get_mantid_version: Mock):
        """
        Test: The flat_output state is respected
        """
        self.message.flat_output = True

        with tempfile.NamedTemporaryFile() as tmpfile:
            self.message.data = tmpfile.name

            runner = ReductionRunner(self.message, self.run_name)
            runner.reduce()

        reduce.assert_called_once()
        _get_mantid_version.assert_called_once()
        assert str(reduce.call_args[0][2][0].path) == tmpfile.name
        assert runner.message.flat_output is True
