# ############################################################################ #
# Autoreduction Repository :
# https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
"""Tests message handling for the queue processor."""
# pylint:disable=no-member,unsupported-membership-test,line-too-long
import random
from functools import partial
from unittest import main, mock
from unittest.mock import Mock, patch

from django.db.utils import IntegrityError
from django.test import TestCase
from parameterized import parameterized

from autoreduce_db.reduction_viewer.models import (Experiment, Instrument, Status, Software)
from autoreduce_utils.message.message import Message
from autoreduce_qp.model.database.records import create_reduction_run_record
from autoreduce_qp.queue_processor.handle_message import HandleMessage
from autoreduce_qp.queue_processor.confluent_consumer import Consumer
from autoreduce_qp.systemtests.utils.data_archive import DefaultDataArchive


def make_test_message(instrument: str) -> Message:
    """Makes a Message object with test values"""
    msg = Message()

    msg.populate({
        "run_number": 7654321,
        "rb_number": 1234567,
        "run_title": "test title",
        "run_version": 0,
        "reduction_data": "/path/1",
        "started_by": -1,
        "data": "/path",
        'software': {
            "name": "Mantid",
            "version": "6.2.0",
        },
        "description": "This is a fake description",
        "instrument": instrument,  # Autoreduction Mock Instrument
        "reduction_script": """def main(input_file, output_dir): print(123)""",
        "reduction_arguments": {
            "standard_vars": {
                "variable": "value"
            }
        }
    })
    return msg


class TestHandleMessage(TestCase):
    """Directly test the message handling classes."""
    fixtures = ["status_fixture"]

    def setUp(self):
        self.mocked_client = mock.Mock(spec=Consumer)
        self.instrument_name = "ARMI"
        self.msg = make_test_message(self.instrument_name)

        with patch("logging.getLogger") as patched_logger:
            self.handler = HandleMessage()
            self.mocked_logger = patched_logger.return_value

        self.experiment, _ = Experiment.objects.get_or_create(reference_number=1231231)
        self.instrument, _ = Instrument.objects.get_or_create(name=self.instrument_name, is_active=True)
        self.software, _ = Software.objects.get_or_create(name="Mantid", version="6.2.0")
        status = Status.get_queued()
        self.reduction_run, self.message = create_reduction_run_record(self.experiment, self.instrument, self.msg, 0,
                                                                       status, self.software)

    @parameterized.expand([
        ["reduction_error", 'e'],
        ["reduction_skipped", 's'],
    ])
    def test_reduction_with_message(self, function_to_call, expected_status):
        """Test a reduction error where the message contains an error message."""
        self.msg.message = "I am a message"
        getattr(self.handler, function_to_call)(self.reduction_run, self.msg)

        # pylint:disable=protected-access
        assert self.reduction_run.status == Status._get_status(expected_status)
        assert self.reduction_run.message == "I am a message"
        assert self.reduction_run.run_description == "This is a fake description"
        assert self.reduction_run.run_title == "test title"
        self.mocked_logger.info.assert_called_once()
        assert self.mocked_logger.info.call_args[0][1] == self.msg.run_number

    @parameterized.expand([
        ["reduction_error", 'e'],
        ["reduction_skipped", 's'],
    ])
    def test_reduction_without_message(self, function_to_call, expected_status):
        """
        Test a reduction error where the message does not contain an error
        message.
        """
        getattr(self.handler, function_to_call)(self.reduction_run, self.msg)

        # pylint:disable=protected-access
        assert self.reduction_run.status == Status._get_status(expected_status)
        self.mocked_logger.info.assert_called_once()
        assert self.mocked_logger.info.call_args[0][1] == self.msg.run_number

    def test_reduction_started(self):
        """Test starting a reduction."""
        assert self.reduction_run.started is None
        assert self.reduction_run.finished is None

        self.handler.reduction_started(self.reduction_run, self.msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is None
        assert self.reduction_run.status == Status.get_processing()
        self.mocked_logger.info.assert_called_once()

    def test_reduction_complete(self):
        """Test completing a reduction."""
        self.msg.reduction_data = None
        assert self.reduction_run.finished is None
        self.handler.reduction_complete(self.reduction_run, self.msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.finished is not None
        assert self.reduction_run.status == Status.get_completed()
        self.mocked_logger.info.assert_called_once()
        assert self.reduction_run.software.name == self.msg.software.get("name")
        assert self.reduction_run.software.version == self.msg.software.get("version")
        assert self.reduction_run.reduction_location.count() == 0

    def test_reduction_complete_with_reduction_data(self):
        """
        Test completing a reduction that has an output location at
        reduction_data.
        """
        assert self.reduction_run.finished is None
        self.handler.reduction_complete(self.reduction_run, self.msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.finished is not None
        assert self.reduction_run.status == Status.get_completed()
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.reduction_location.first().file_path == "/path/1"

    @patch("autoreduce_qp.queue_processor.handle_message.ReductionProcessManager")
    def test_do_reduction_success(self, rpm):
        """Test the success path of do_reduction."""
        rpm.return_value.run = self.do_post_started_assertions

        self.handler.do_reduction(self.reduction_run, self.msg, self.software)
        assert self.reduction_run.status == Status.get_completed()
        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is not None
        assert self.reduction_run.reduction_location.first().file_path == "/path/1"

    @patch("autoreduce_qp.queue_processor.handle_message.ReductionProcessManager")
    def test_do_reduction_success_batch_run(self, rpm: Mock):
        """Test the success path of do_reduction."""
        rpm.return_value.run = self.do_post_started_assertions
        self.reduction_run.batch_run = True
        self.reduction_run.run_numbers.create(run_number=7654322)

        self.handler.do_reduction(self.reduction_run, self.msg, self.software)
        rpm.assert_called_once_with(self.msg, "batch-7654321-7654322", self.software)
        assert self.reduction_run.status == Status.get_completed()
        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is not None
        assert self.reduction_run.reduction_location.first().file_path == "/path/1"

    @patch("autoreduce_qp.queue_processor.handle_message.ReductionProcessManager")
    def test_do_reduction_success_special_characters_in_script(self, rpm):
        """
        Test the success path of do_reduction with special characters in the
        script.
        """
        rpm.return_value.run = self.do_post_started_assertions
        test_special_chars_script = 'print("✈", "’")'
        self.reduction_run.script.text = test_special_chars_script

        self.handler.do_reduction(self.reduction_run, self.msg, self.software)
        assert self.reduction_run.status == Status.get_completed()
        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is not None
        assert self.reduction_run.reduction_location.first().file_path == "/path/1"
        assert self.reduction_run.script.text == test_special_chars_script

    def do_post_started_assertions(self, expected_info_calls=1):
        "Helper method to capture common assertions between tests."
        assert self.reduction_run.status == Status.get_processing()
        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is None
        assert self.mocked_logger.info.call_count == expected_info_calls
        # Reset for follow logger calls
        self.mocked_logger.info.reset_mock()
        return self.msg

    # A bit of a nasty patch, but everything underneath should be unit tested separately
    @patch("autoreduce_qp.queue_processor.handle_message.ReductionProcessManager")
    def test_do_reduction_fail(self, rpm):
        "Test do_reduction failure path."
        self.msg.message = "Something failed"

        rpm.return_value.run = self.do_post_started_assertions

        self.handler.do_reduction(self.reduction_run, self.msg, self.software)
        assert self.reduction_run.status == Status.get_error()
        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is not None
        assert self.reduction_run.message == "Something failed"

    def test_activate_db_inst(self):
        """Test that the function enables the instrument."""
        self.instrument.is_active = False
        self.instrument.save()

        self.handler.activate_db_inst(self.instrument)

        assert self.instrument.is_active

    def test_find_reason_to_skip_run_empty_script(self):
        """
        Test find_reason_to_skip_run correctly captures validation failing on
        the message.
        """
        self.reduction_run.script.text = ""
        reason = self.handler.find_reason_to_skip_run(self.reduction_run, self.msg, self.instrument)

        assert reason
        assert "Script text for current instrument is empty" in reason

    def test_find_reason_to_skip_run_message_validation_fails(self):
        """
        Test that find_reason_to_skip_run correctly captures validation failing
        on the message.
        """
        self.msg.rb_number = 123  # invalid RB number, should be 7 digits
        assert "Validation error" in self.handler.find_reason_to_skip_run(self.reduction_run, self.msg, self.instrument)

    def test_find_reason_to_skip_run_instrument_paused(self):
        """
        Test that find_reason_to_skip_run correctly captures that the instrument
        is paused.
        """
        self.instrument.is_paused = True
        assert "is paused" in self.handler.find_reason_to_skip_run(self.reduction_run, self.msg, self.instrument)

    def test_find_reason_to_skip_run_instrument_inactive(self):
        """
        Test that find_reason_to_skip_run returns an error string when an
        instrument's is_active flag is False.
        """
        self.instrument.is_active = False
        assert "is inactive" in self.handler.find_reason_to_skip_run(self.reduction_run, self.msg, self.instrument)

    def test_find_reason_to_skip_run_doesnt_skip_when_all_is_ok(self):
        """
        Test that find_reason_to_skip_run returns None when all the validation
        passes.
        """
        assert self.handler.find_reason_to_skip_run(self.reduction_run, self.msg, self.instrument) is None

    @patch("autoreduce_qp.queue_processor.handle_message.ReductionProcessManager")
    def test_send_message_onwards_ok(self, rpm):
        """Test that a run where all is OK is reduced."""
        rpm.return_value.run = partial(self.do_post_started_assertions)

        self.handler.send_message_onwards(self.reduction_run, self.msg, self.instrument, self.software)

        assert self.reduction_run.status == Status.get_completed()
        assert self.instrument.is_active

    @patch("autoreduce_qp.queue_processor.handle_message.ReductionProcessManager")
    def test_send_message_onwards_skip_run(self, rpm):
        """Test that a run that fails validation is skipped."""
        self.msg.rb_number = 123

        self.handler.send_message_onwards(self.reduction_run, self.msg, self.instrument, self.software)

        rpm.return_value.run.assert_not_called()
        assert self.reduction_run.status == Status.get_skipped()
        assert "Validation error" in self.reduction_run.message
        assert "Validation error" in self.reduction_run.reduction_log

    def test_create_run_records_multiple_versions(self):
        """Test creating multiple version of the same run."""
        self.instrument.is_active = False

        self.msg.description = "Testing multiple versions"

        self.msg.run_number = random.randint(1000000, 10000000)
        for i in range(5):
            reduction_run, message, instrument, software = self.handler.create_run_records(self.msg)

            assert reduction_run.run_number == self.msg.run_number
            assert reduction_run.experiment.reference_number == self.msg.rb_number
            assert reduction_run.run_version == i
            assert reduction_run.run_description == "Testing multiple versions"
            assert message.run_version == i
            assert instrument == self.instrument
            assert instrument.name == self.msg.instrument
            assert reduction_run.script.text == self.msg.reduction_script
            assert reduction_run.arguments.as_dict() == self.msg.reduction_arguments
            assert reduction_run.data_location.first().file_path == message.data
            assert reduction_run.status == Status.get_queued()
            assert software.name == self.msg.software["name"]
            assert software.version == self.msg.software["version"]

    def test_data_ready_other_exception_raised_ends_processing(self):
        """Test an exception being raised inside data_ready handler."""
        self.handler.create_run_records = Mock(side_effect=RuntimeError)
        with self.assertRaises(RuntimeError):
            self.handler.data_ready(self.msg)
        self.mocked_logger.info.assert_called_once()
        self.mocked_logger.error.assert_called_once()

    def test_data_ready_variable_integrity_error_marks_reduction_error(self):
        """
        Test that an integrity error inside data_ready marks the reduction as
        errored.
        """
        self.handler.create_run_records = Mock(return_value=(self.reduction_run, self.msg, self.instrument,
                                                             self.software))
        self.handler.send_message_onwards = Mock(side_effect=IntegrityError)
        with self.assertRaises(IntegrityError):
            self.handler.data_ready(self.msg)
        assert self.mocked_logger.info.call_count == 2
        self.mocked_logger.error.assert_called_once()
        assert self.reduction_run.status == Status.get_error()
        assert "Encountered error when saving run variables" in self.reduction_run.message

    def test_create_run_records_invalid_rb_number(self):
        """Test creating a run record when the rb number is invalid."""
        with DefaultDataArchive(self.instrument_name):
            self.msg.rb_number = "INVALID RB NUMBER CALIBRATION RUN PERHAPS"
            reduction_run, _, _, _ = self.handler.create_run_records(self.msg)
            assert reduction_run.experiment.reference_number == 0

    def test_create_run_records_valid_rb_number(self):
        """Test creating a run record when the rb number is invalid."""
        with DefaultDataArchive(self.instrument_name):
            reduction_run, _, _, _ = self.handler.create_run_records(self.msg)
            assert reduction_run.experiment.reference_number == self.msg.rb_number

    @patch("autoreduce_qp.queue_processor.handle_message.records.VariableUtils.get_default_variables")
    def test_valid_url_paths(self, load: Mock):
        """
        Test that fetch_from_remote_source() correctly returns None when valid
        arguments are supplied.
        """
        self.msg.reduction_arguments = None
        load.return_value = {
            "advanced_vars": {
                "monovan_mapfile": {
                    "url":
                    "https://raw.githubusercontent.com/mantidproject/scriptrepository/master/direct_inelastic/MARI/MapFiles/",
                    "default": "mari_res2013.map"
                },
                "hard_mask_file": {
                    "url":
                    "https://raw.githubusercontent.com/mantidproject/scriptrepository/master/direct_inelastic/MARI/MaskFiles/",
                    "default": "mari_mask2015_3.msk"
                }
            }
        }
        _, message = self.handler.data_ready(self.msg)
        assert message.message is None

    @patch("autoreduce_qp.queue_processor.handle_message.records.VariableUtils.get_default_variables")
    def test_single_invalid_filename(self, load: Mock):
        """
        Test that fetch_from_remote_source() returns an error string containing
        the path to missing_file.msk.
        """
        self.msg.reduction_arguments = None
        load.return_value = {
            "advanced_vars": {
                "monovan_mapfile": {
                    "url":
                    "https://raw.githubusercontent.com/mantidproject/scriptrepository/master/direct_inelastic/MARI/MapFiles/",
                    "default": "mari_res2013.map"
                },
                "hard_mask_file": {
                    "url":
                    "https://raw.githubusercontent.com/mantidproject/scriptrepository/master/direct_inelastic/MARI/MaskFiles/",
                    "default": "missing_file.msk"
                }
            }
        }
        reduction_run, message = self.handler.data_ready(self.msg)
        assert "missing_file.msk" in message.message
        assert reduction_run.message == message.message

    @patch("autoreduce_qp.queue_processor.handle_message.records.VariableUtils.get_default_variables")
    def test_multiple_invalid_filenames(self, load: Mock):
        """
        Test that fetch_from_remote_source() returns an error string containing
        the path to not_found_file.map AND the path to missing_file.msk.
        """
        self.msg.reduction_arguments = None
        load.return_value = {
            "advanced_vars": {
                "monovan_mapfile": {
                    "url":
                    "https://raw.githubusercontent.com/mantidproject/scriptrepository/master/direct_inelastic/MARI/MapFiles/",
                    "default": "not_found_file.map"
                },
                "hard_mask_file": {
                    "url":
                    "https://raw.githubusercontent.com/mantidproject/scriptrepository/master/direct_inelastic/MARI/MaskFiles/",
                    "default": "missing_file.msk"
                }
            }
        }
        reduction_run, message = self.handler.data_ready(self.msg)
        assert all(text in message.message for text in ("not_found_file.map", "missing_file.msk"))
        assert reduction_run.message == message.message

    @patch("autoreduce_qp.queue_processor.handle_message.records.VariableUtils.get_default_variables")
    def test_missing_file_paths(self, load: Mock):
        """
        Test that fetch_from_remote_source() returns an error string containing
        the details about files missing "url" and "default" keys.
        """
        self.msg.reduction_arguments = None
        load.return_value = {
            "advanced_vars": {
                "monovan_mapfile": {
                    "url":
                    "https://raw.githubusercontent.com/mantidproject/scriptrepository/master/direct_inelastic/MARI/MapFiles/",
                },
                "hard_mask_file": {
                    "default": "mari_mask2015_3.msk"
                }
            }
        }
        reduction_run, message = self.handler.data_ready(self.msg)
        assert "no file name supplied for monovan_mapfile under advanced_vars" in message.message.lower()
        assert "no path supplied for hard_mask_file under advanced_vars" in message.message.lower()
        assert reduction_run.message == message.message


if __name__ == '__main__':
    main()
