# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
"""
Tests message handling for the queue processor
"""

import pytest
from queue_processors.queue_processor.queueproc_utils.tests.test_instrument_variable_utils import FakeModule
import unittest
from unittest import mock
from unittest.mock import patch

import model.database.access
from model.database.records import create_reduction_run_record
from model.message.message import Message
from queue_processors.queue_processor._utils_classes import _UtilsClasses
from queue_processors.queue_processor.handle_message import HandleMessage
from queue_processors.queue_processor.queue_listener import QueueListener
from parameterized import parameterized

utils = _UtilsClasses()


class FakeMessage:
    started_by = 0
    run_number = 1234567
    message = "I am a message"


# @patch("queue_processors.queue_processor.handle_message.db_access", spec=access)
class TestHandleMessage(unittest.TestCase):
    """
    Directly tests the message handling classes
    """

    # pylint: disable=arguments-differ
    # @patch("queue_processors.queue_processor.handle_message._UtilsClasses")
    # @patch("queue_processors.queue_processor.handle_message.db_records")
    # @patch("logging.getLogger")
    # def setUp(self, log_const, db_records, util_const):
    def setUp(self):
        # self.db_records = db_records
        self.mocked_client = mock.Mock(spec=QueueListener)
        # self.mocked_utils = mock.MagicMock(spec=_UtilsClasses)
        # util_const.return_value = self.mocked_utils

        self._utils = _UtilsClasses()

        with patch("logging.getLogger") as patched_logger:
            self.handler = HandleMessage(self.mocked_client)
            self.mocked_logger = patched_logger.return_value

        db_handle = model.database.access.start_database()
        self.data_model = db_handle.data_model
        self.variable_model = db_handle.variable_model

        self.experiment = self.data_model.Experiment.objects.create(reference_number=1231231)
        self.instrument = self.data_model.Instrument.objects.create(name="MyInstrument", is_active=1, is_paused=0)
        status = self.data_model.Status.objects.get(value="q")
        fake_script_text = "scripttext"
        self.reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                         fake_script_text, status)
        self.reduction_run.save()

    def tearDown(self) -> None:
        self.experiment.delete()
        self.instrument.delete()
        self.reduction_run.delete()

    @parameterized.expand([
        ["reduction_error", utils.status.get_error()],
        ["reduction_skipped", utils.status.get_skipped()],
    ])
    def test_reduction_with_message(self, callable, expected_status):
        """
        Tests a reduction error where the message contains an error message
        """
        msg = Message()
        msg.populate({"message": "I am a message", "run_number": 7654321})
        getattr(self.handler, callable)(self.reduction_run, msg)

        assert self.reduction_run.status == expected_status
        assert self.reduction_run.message == "I am a message"
        self.mocked_logger.info.assert_called_once()
        assert self.mocked_logger.info.call_args[0][1] == msg.run_number

    @parameterized.expand([
        ["reduction_error", utils.status.get_error()],
        ["reduction_skipped", utils.status.get_skipped()],
    ])
    def test_reduction_with_message(self, callable, expected_status):
        """
        Tests a reduction error where the message contains an error message
        """
        msg = Message()
        msg.populate({"message": "I am a message", "run_number": 7654321})
        getattr(self.handler, callable)(self.reduction_run, msg)

        assert self.reduction_run.status == expected_status
        assert self.reduction_run.message == "I am a message"
        self.mocked_logger.info.assert_called_once()
        assert self.mocked_logger.info.call_args[0][1] == msg.run_number

    @parameterized.expand([
        ["reduction_error", utils.status.get_error()],
        ["reduction_skipped", utils.status.get_skipped()],
    ])
    def test_reduction_without_message(self, callable, expected_status):
        """
        Tests a reduction error where the message does not contain an error message
        """
        msg = Message()
        msg.populate({"run_number": 7654321})
        getattr(self.handler, callable)(self.reduction_run, msg)

        assert self.reduction_run.status == expected_status
        self.mocked_logger.info.assert_called_once()
        assert self.mocked_logger.info.call_args[0][1] == msg.run_number

    def test_reduction_started(self):
        msg = Message()
        msg.populate({"run_number": 7654321, "rb_number": 1234567, "run_version": 0})
        assert self.reduction_run.started is None
        assert self.reduction_run.finished is None

        self.handler.reduction_started(self.reduction_run, msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is None
        assert self.reduction_run.status == utils.status.get_processing()
        self.mocked_logger.info.assert_called_once()

    def test_reduction_complete(self):
        msg = Message()
        msg.populate({"run_number": 7654321, "rb_number": 1234567, "run_version": 0})
        assert self.reduction_run.finished is None
        self.handler.reduction_complete(self.reduction_run, msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.finished is not None
        assert self.reduction_run.status == utils.status.get_completed()
        self.mocked_logger.info.assert_called_once()

    def test_reduction_complete_with_reduction_data(self):
        msg = Message()
        msg.populate({
            "run_number": 7654321,
            "rb_number": 1234567,
            "run_version": 0,
            "reduction_data": ["/path/1", "/path/2"]
        })
        assert self.reduction_run.finished is None
        self.handler.reduction_complete(self.reduction_run, msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.finished is not None
        assert self.reduction_run.status == utils.status.get_completed()
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.reduction_location.first().file_path == "/path/1"
        assert self.reduction_run.reduction_location.last().file_path == "/path/2"

    def test_do_reduction_success(self):
        msg = Message()
        msg.populate({
            "run_number": 7654321,
            "rb_number": 1234567,
            "run_version": 0,
            "reduction_data": ["/path/1", "/path/2"]
        })

        # a bit of a nasty patch, but everything underneath should be unit tested separately
        with patch("queue_processors.queue_processor.handle_message.ReductionProcessManager") as rpm:

            def do_post_started_assertions():
                assert self.reduction_run.status == utils.status.get_processing()
                assert self.reduction_run.started is not None
                assert self.reduction_run.finished is None
                self.mocked_logger.info.assert_called_once()
                # reset for follow logger calls
                self.mocked_logger.info.reset_mock()
                return msg

            rpm.return_value.run = do_post_started_assertions

            self.handler.do_reduction(self.reduction_run, msg)
            assert self.reduction_run.status == utils.status.get_completed()
            assert self.reduction_run.started is not None
            assert self.reduction_run.finished is not None
            assert self.reduction_run.reduction_location.first().file_path == "/path/1"
            assert self.reduction_run.reduction_location.last().file_path == "/path/2"

    def test_do_reduction_fail(self):
        msg = Message()
        msg.populate({
            "run_number": 7654321,
            "rb_number": 1234567,
            "run_version": 0,
            "reduction_data": ["/path/1", "/path/2"],
            "message": "Something failed"
        })

        # a bit of a nasty patch, but everything underneath should be unit tested separately
        with patch("queue_processors.queue_processor.handle_message.ReductionProcessManager") as rpm:

            def do_post_started_assertions():
                assert self.reduction_run.status == utils.status.get_processing()
                assert self.reduction_run.started is not None
                assert self.reduction_run.finished is None
                self.mocked_logger.info.assert_called_once()
                # reset for follow logger calls
                self.mocked_logger.info.reset_mock()
                return msg

            rpm.return_value.run = do_post_started_assertions

            self.handler.do_reduction(self.reduction_run, msg)
            assert self.reduction_run.status == utils.status.get_error()
            assert self.reduction_run.started is not None
            assert self.reduction_run.finished is not None
            assert self.reduction_run.message == "Something failed"

    def test_activate_db_inst(self):
        self.instrument.is_active = False
        self.instrument.save()

        self.handler.activate_db_inst(self.instrument)

        assert self.instrument.is_active


# TODO test that instrument is not enabled when it's reduce.py script is missing
if __name__ == '__main__':
    unittest.main()
