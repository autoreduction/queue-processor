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

import unittest
from unittest import mock
from unittest.mock import patch
from parameterized import parameterized

import model.database.access
from model.database.records import create_reduction_run_record
from model.message.message import Message
from queue_processors.queue_processor._utils_classes import _UtilsClasses
from queue_processors.queue_processor.handle_message import HandleMessage
from queue_processors.queue_processor.queue_listener import QueueListener

utils = _UtilsClasses()


class FakeMessage:
    started_by = 0
    run_number = 1234567
    message = "I am a message"


class TestHandleMessage(unittest.TestCase):
    """
    Directly tests the message handling classes
    """
    def setUp(self):
        self.mocked_client = mock.Mock(spec=QueueListener)

        self._utils = _UtilsClasses()
        self.msg = Message()
        self.msg.populate({
            "run_number": 7654321,
            "rb_number": 1234567,
            "run_version": 0,
            "reduction_data": "/path/1",
            "started_by": -1,
            "data": "/path"
        })
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
        self.msg.message = "I am a message"
        getattr(self.handler, callable)(self.reduction_run, self.msg)

        assert self.reduction_run.status == expected_status
        assert self.reduction_run.message == "I am a message"
        self.mocked_logger.info.assert_called_once()
        assert self.mocked_logger.info.call_args[0][1] == self.msg.run_number

    @parameterized.expand([
        ["reduction_error", utils.status.get_error()],
        ["reduction_skipped", utils.status.get_skipped()],
    ])
    def test_reduction_without_message(self, callable, expected_status):
        """
        Tests a reduction error where the message does not contain an error message
        """
        getattr(self.handler, callable)(self.reduction_run, self.msg)

        assert self.reduction_run.status == expected_status
        self.mocked_logger.info.assert_called_once()
        assert self.mocked_logger.info.call_args[0][1] == self.msg.run_number

    def test_reduction_started(self):
        assert self.reduction_run.started is None
        assert self.reduction_run.finished is None

        self.handler.reduction_started(self.reduction_run, self.msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is None
        assert self.reduction_run.status == utils.status.get_processing()
        self.mocked_logger.info.assert_called_once()

    def test_reduction_complete(self):
        assert self.reduction_run.finished is None
        self.handler.reduction_complete(self.reduction_run, self.msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.finished is not None
        assert self.reduction_run.status == utils.status.get_completed()
        self.mocked_logger.info.assert_called_once()

    def test_reduction_complete_with_reduction_data(self):
        assert self.reduction_run.finished is None
        self.handler.reduction_complete(self.reduction_run, self.msg)
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.finished is not None
        assert self.reduction_run.status == utils.status.get_completed()
        self.mocked_logger.info.assert_called_once()

        assert self.reduction_run.reduction_location.first().file_path == "/path/1"

    def test_do_reduction_success(self):
        # a bit of a nasty patch, but everything underneath should be unit tested separately
        with patch("queue_processors.queue_processor.handle_message.ReductionProcessManager") as rpm:

            def do_post_started_assertions():
                assert self.reduction_run.status == utils.status.get_processing()
                assert self.reduction_run.started is not None
                assert self.reduction_run.finished is None
                self.mocked_logger.info.assert_called_once()
                # reset for follow logger calls
                self.mocked_logger.info.reset_mock()
                return self.msg

            rpm.return_value.run = do_post_started_assertions

            self.handler.do_reduction(self.reduction_run, self.msg)
            assert self.reduction_run.status == utils.status.get_completed()
            assert self.reduction_run.started is not None
            assert self.reduction_run.finished is not None
            assert self.reduction_run.reduction_location.first().file_path == "/path/1"

    def do_post_started_assertions(self):
        assert self.reduction_run.status == utils.status.get_processing()
        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is None
        self.mocked_logger.info.assert_called_once()
        # reset for follow logger calls
        self.mocked_logger.info.reset_mock()
        return self.msg

    # a bit of a nasty patch, but everything underneath should be unit tested separately
    @patch("queue_processors.queue_processor.handle_message.ReductionProcessManager")
    def test_do_reduction_fail(self, rpm):
        self.msg.message = "Something failed"

        rpm.return_value.run = self.do_post_started_assertions

        self.handler.do_reduction(self.reduction_run, self.msg)
        assert self.reduction_run.status == utils.status.get_error()
        assert self.reduction_run.started is not None
        assert self.reduction_run.finished is not None
        assert self.reduction_run.message == "Something failed"

    def test_activate_db_inst(self):
        self.instrument.is_active = False
        self.instrument.save()

        self.handler.activate_db_inst(self.instrument)

        assert self.instrument.is_active

    def test_should_skip_message_validation_fails(self):
        """
        Test should_skip correctly captures validation failing on the message
        """
        self.msg.rb_number = 123  # invalid RB number, should be 7 digits
        assert "Validation error" in self.handler.should_skip(self.msg, self.instrument)

    def test_should_skip_instrument_paused(self):
        """
        Test should_skip correctly captures that the instrument is paused
        """
        self.instrument.is_paused = True

        assert "is paused" in self.handler.should_skip(self.msg, self.instrument)

    def test_should_skip_doesnt_skip_when_all_is_ok(self):
        """
        Test should_skip returns None when all the validation passes
        """
        assert self.handler.should_skip(self.msg, self.instrument) is None

    @patch("queue_processors.queue_processor.handle_message.ReductionProcessManager")
    def test_send_message_onwards_ok(self, rpm):
        """
        Test that a run where all is OK is reduced
        """
        rpm.return_value.run = self.do_post_started_assertions

        self.handler.send_message_onwards(self.reduction_run, self.msg, self.instrument)

        assert self.reduction_run.status == utils.status.get_completed()

    @patch("queue_processors.queue_processor.handle_message.ReductionProcessManager")
    def test_send_message_onwards_skip_run(self, rpm):
        """
        Test that a run that fails validation is skipped
        """
        self.msg.rb_number = 123

        self.handler.send_message_onwards(self.reduction_run, self.msg, self.instrument)

        rpm.return_value.run.assert_not_called()
        assert self.reduction_run.status == utils.status.get_skipped()
        assert "Validation error" in self.reduction_run.message


# TODO test that instrument is not enabled when it's reduce.py script is missing
if __name__ == '__main__':
    unittest.main()
