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

from model.message.job import Message
from pipeline.queue import handle_message
from pipeline.queue._utils_classes import _UtilsClasses
from pipeline.queue.handle_message import HandleMessage
from pipeline.queue.handling_exceptions import \
    InvalidStateException, MissingReductionRunRecord, MissingExperimentRecord
from pipeline.queue.stomp_client import StompClient
from utils.settings import ACTIVEMQ_SETTINGS

# Disable warnings which don't really apply to test classes
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods


class TestHandleMessageFreeFuncs(unittest.TestCase):
    """
    Tests the free functions in Queue Processor
    """
    def test_is_valid_rb(self):
        """
        Tests the valid and invalid cases for RB numbers
        """
        valid_values = [1, 20, "10000"]
        for i in valid_values:
            self.assertIsNone(handle_message.validate_rb_num(i))

        invalid_values = [0, 0.1, -1, -100, None, "foo"]
        for i in invalid_values:
            with self.assertRaises(InvalidStateException):
                handle_message.validate_rb_num(i)


@patch("pipeline.queue.handle_message.db_access")
class TestHandleMessage(unittest.TestCase):
    """
    Directly tests the message handling classes
    """

    # pylint: disable=arguments-differ
    @patch("pipeline.queue.handle_message._UtilsClasses")
    @patch("logging.getLogger")
    def setUp(self, log_const, util_const):
        self.mocked_client = mock.Mock(spec=StompClient)
        self.mocked_utils = mock.MagicMock(spec=_UtilsClasses)
        util_const.return_value = self.mocked_utils

        self.handler = HandleMessage(self.mocked_client)
        self.mocked_logger = log_const.return_value

    @staticmethod
    def _get_mocked_db_return_vals(mock_instrument, mock_data_location,
                                   mock_new_reduction_run,
                                   mock_existing_reduction_run):
        return {"get_instrument.return_value": mock_instrument,

                "start_database.return_value.data_model"
                ".DataLocation.return_value": mock_data_location,
                "start_database.return_value.data_model"
                ".ReductionRun.return_value": mock_new_reduction_run,

                # Chained calls makes this painful
                # TODO replace with method we can just patch
                "start_database.return_value.data_model"
                ".ReductionRun.objects"
                ".filter.return_value"
                ".filter.return_value"
                ".order_by.return_value"
                ".first.return_value": mock_existing_reduction_run}

    @staticmethod
    def _get_mock_message():
        mocked_message = mock.Mock(spec=Message())
        mocked_message.rb_number = 1
        return mocked_message

    def test_data_model_only_inits_once(self, patched_db):
        """
        Tests that the data model property only performs the init once,
        then holds onto and returns the same instance again
        """
        model_mock = patched_db.start_database.return_value.data_model
        first_call = self.handler._data_model
        patched_db.start_database.assert_called_once()
        self.assertEqual(model_mock, first_call)

        patched_db.start_database.reset_mock()
        second_call = self.handler._data_model
        patched_db.start_database.assert_not_called()
        self.assertEqual(first_call, second_call)

    def test_data_ready_marks_inst_active(self, patched_db):
        """
        Tests that calling data ready on an inactive instrument record
        updates the record to become active
        """
        self.mocked_utils.reduction_run. \
            get_script_and_arguments.return_value = (mock.NonCallableMock(),
                                                     mock.NonCallableMock())

        mock_inst_record = mock.NonCallableMock()
        mock_inst_record.is_active = 0

        patched_db.configure_mock(**self._get_mocked_db_return_vals(
            # We only care about the inst record being modified / saved
            mock_instrument=mock_inst_record,
            mock_new_reduction_run=mock.Mock(),
            mock_existing_reduction_run=None,
            mock_data_location=None
        ))

        self.handler.data_ready(message=self._get_mock_message())
        self.assertEqual(1, mock_inst_record.is_active)
        patched_db.save_record.assert_any_call(mock_inst_record)

    def test_data_ready_constructs_reduction_record(self, patched_db):
        """
        Tests the calling data ready with an instrument that does not
        exist in the DB creates the record
        """
        self.mocked_utils.reduction_run. \
            get_script_and_arguments.return_value = (mock.NonCallableMock(),
                                                     mock.NonCallableMock())

        # This method should not cap our highest version
        highest_version = 100
        mock_existing_run = mock.Mock()
        mock_existing_run.run_version = highest_version

        mock_experiment = mock.NonCallableMock()
        mock_instrument = mock.NonCallableMock()
        patched_db.get_experiment.return_value = mock_experiment

        input_expected = [(None, 0),
                          (mock_existing_run, highest_version + 1)]

        for mock_in, expected_vers in input_expected:
            patched_db.configure_mock(**self._get_mocked_db_return_vals(
                mock_instrument=mock_instrument,
                mock_new_reduction_run=mock.NonCallableMock(),
                mock_existing_reduction_run=mock_in,
                mock_data_location=mock.NonCallableMock()
            ))
            mock_reduction_constructor = \
                patched_db.start_database.return_value.data_model.ReductionRun
            mock_reduction_constructor.reset_mock()

            mock_message = self._get_mock_message()
            self.handler.data_ready(message=mock_message)

            # TODO we are def passing too much in here
            mock_reduction_constructor.assert_called_once_with(
                run_name='', cancel=0, hidden_in_failviewer=0,
                admin_log='', reduction_log='',
                created=mock.ANY, last_updated=mock.ANY,
                run_version=expected_vers,
                # Mocked inputs below
                run_number=mock_message.run_number,
                experiment_id=mock_experiment.id,
                instrument_id=mock_instrument.id,
                status_id=self.mocked_utils.status.get_skipped().id,
                script=self.mocked_utils.instrument_variable
                .get_current_script_text()[0],
                started_by=mock_message.started_by)

    def test_data_ready_skips_paused_inst(self, patched_db):
        """
        Tests that calling data ready on a paused instrument does
        not queue up that data for processing and instead skips it
        """
        self.mocked_utils.reduction_run. \
            get_script_and_arguments.return_value = (mock.NonCallableMock(),
                                                     mock.NonCallableMock())

        mock_reduction_run = mock.Mock()
        mock_instrument = mock.Mock()
        mock_instrument.is_paused = True

        patched_db.configure_mock(**self._get_mocked_db_return_vals(
            mock_instrument=mock_instrument,
            mock_data_location=mock.Mock(),
            mock_new_reduction_run=mock_reduction_run,
            mock_existing_reduction_run=None
        ))

        self.mocked_client.send_message.assert_not_called()

    def test_data_ready_empty_script_calls_error(self, patched_db):
        """
        Tests that calling data empty with an empty script will
        throw an exception noting that the script text was empty.
        """
        patched_db.configure_mock(**self._get_mocked_db_return_vals(
            mock_data_location=mock.Mock(),
            mock_new_reduction_run=mock.Mock(),
            mock_existing_reduction_run=None,
            mock_instrument=mock.Mock()))

        self.handler.reduction_error = mock.Mock()
        self.mocked_utils.instrument_variable\
            .get_current_script_text.return_value = [None]

        with self.assertRaises(InvalidStateException):
            self.handler.data_ready(self._get_mock_message())
        self.handler.reduction_error.assert_called_once()

    @patch("pipeline.queue.handle_message.validate_rb_num")
    def test_data_ready_with_new_data(self, _, patched_db):
        """
        Tests the ideal flow for data ready, where we will queue up
        actual data for processing
        """
        mock_instrument = mock.NonCallableMock()
        mock_instrument.is_active = True
        mock_instrument.is_paused = False

        mock_data_location = mock.NonCallableMock()
        mock_reduction_run = mock.NonCallableMock()
        mock_script_and_args = (mock.NonCallableMock(), mock.NonCallableMock())

        self.mocked_utils.reduction_run. \
            get_script_and_arguments.return_value = mock_script_and_args

        db_return_values = \
            self._get_mocked_db_return_vals(mock_instrument,
                                            mock_data_location,
                                            mock_reduction_run,
                                            mock_existing_reduction_run=None)
        patched_db.configure_mock(**db_return_values)

        # Run
        mocked_msg = self._get_mock_message()
        self.handler.data_ready(message=mocked_msg)

        # Assert Database accesses
        patched_db.get_instrument.assert_called_with(
            str(mocked_msg.instrument), create=True)
        patched_db.get_experiment.assert_called_with(
            mocked_msg.rb_number, create=True)
        patched_db.save_record.assert_any_call(mock_data_location)
        patched_db.save_record.assert_any_call(mock_reduction_run)

        # Assert utils used correctly
        self.mocked_utils.status.get_queued.assert_called_once()

        self.mocked_utils.instrument_variable.get_current_script_text. \
            assert_called_once_with(mock_instrument.name)
        self.mocked_utils.instrument_variable.create_variables_for_run. \
            assert_called_once_with(mock_reduction_run)

        self.mocked_utils.reduction_run.get_script_and_arguments. \
            assert_called_once_with(mock_reduction_run)

        # Check message is packed correctly
        # Since we set existing run_version to None this will be 0
        self.assertEqual(0, mocked_msg.run_version)
        self.assertEqual(mock_script_and_args[0],
                         mocked_msg.reduction_script)
        self.assertEqual(mock_script_and_args[1],
                         mocked_msg.reduction_arguments)

        # Finally check if the data is sent
        self.mocked_client.send_message.assert_called_once_with(
            "/queue/ReductionPending", mocked_msg)

    def test_reduction_started(self, patched_db):
        """
        Tests the reduction started message handler with valid data
        """
        mock_reduction_record = mock.NonCallableMock()
        self.handler.find_run = mock.Mock(return_value=mock_reduction_record)

        valid_states = ["Error", "Queued"]
        for state in valid_states:
            mock_reduction_record.status.value = state
            self.handler.reduction_started(message=self._get_mock_message())

            self.mocked_utils.status.get_processing.assert_called_once()
            self.assertEqual(self.mocked_utils.status.get_processing(),
                             mock_reduction_record.status)
            patched_db.save_record.called_once_with(mock_reduction_record)

            self.mocked_utils.status.get_processing.reset_mock()
            patched_db.save_record.reset_mock()

    def test_reduction_started_missing_record(self, patched_db):
        """
        Tests reduction started with a missing DB record throws
        """
        self.handler.find_run = mock.Mock(return_value=None)
        with self.assertRaises(MissingReductionRunRecord):
            self.handler.reduction_started(message=self._get_mock_message())

        self.mocked_utils.status.get_processing.assert_not_called()
        patched_db.save_record.assert_not_called()

    def test_reduction_started_invalid_state(self, _):
        """
        Tests reduction started throws if the record state in not expected
        """
        reduction_run_record = mock.NonCallableMock()
        reduction_run_record.state.value = "Unknown"
        self.handler.find_run = mock.Mock(return_value=reduction_run_record)

        with self.assertRaises(InvalidStateException):
            self.handler.reduction_started(self._get_mock_message())

    def test_reduction_complete(self, patched_db):
        """
        Tests reduction complete handler in valid conditions
        """
        mocked_msg = self._get_mock_message()
        mocked_msg.reduction_data = None
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Processing"
        self.handler.find_run = mock.Mock(return_value=mock_reduction_record)

        self.handler.reduction_complete(message=mocked_msg)

        self.assertEqual(self.mocked_utils.status.get_completed(),
                         mock_reduction_record.status)
        self.assertEqual(mocked_msg.message,
                         mock_reduction_record.message)
        self.assertEqual(mocked_msg.reduction_log,
                         mock_reduction_record.reduction_log)
        self.assertEqual(mocked_msg.admin_log,
                         mock_reduction_record.admin_log)

        patched_db.save_record.assert_called_once_with(mock_reduction_record)

    def test_reduction_complete_saves_location_records(self, patched_db):
        """
        Tests reduction complete saves location records if they are available
        to the database
        """
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Processing"
        self.handler.find_run = mock.Mock(return_value=mock_reduction_record)

        location_records = [mock.NonCallableMock(), mock.NonCallableMock()]
        mocked_msg = self._get_mock_message()
        mocked_msg.reduction_data = location_records

        mocked_reduction_location = mock.NonCallableMock()
        patched_db.start_database.return_value.data_model.\
            ReductionLocation.return_value = mocked_reduction_location

        self.handler.reduction_complete(message=mocked_msg)
        patched_db.save_record.assert_any_call(mocked_reduction_location)
        # n - Location records, +1 for Reduction Run Record
        self.assertEqual(len(location_records) + 1,
                         patched_db.save_record.call_count)

    def test_reduction_complete_with_invalid_state(self, patched_db):
        """
        Tests reduction complete throws if the reduction record is invalid
        """
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Unknown"
        self.handler.find_run = mock.Mock(return_value=mock_reduction_record)

        with self.assertRaises(InvalidStateException):
            self.handler.reduction_complete(message=self._get_mock_message())
        patched_db.save_record.assert_not_called()

    def test_reduction_complete_with_missing_record(self, patched_db):
        """
        Tests reduction complete throws if the reduction record is missing
        """
        self.handler.find_run = mock.Mock(return_value=None)

        with self.assertRaises(MissingReductionRunRecord):
            self.handler.reduction_complete(message=self._get_mock_message())
        patched_db.save_record.assert_not_called()

    def test_reduction_skipped(self, patched_db):
        """
        Tests reduction skipped handler in valid conditions
        """
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Processing"
        self.handler.find_run = mock.Mock(return_value=mock_reduction_record)

        mock_msg = self._get_mock_message()

        self.handler.reduction_skipped(message=mock_msg)
        self.assertEqual(self.mocked_utils.status.get_skipped(),
                         mock_reduction_record.status)
        self.assertEqual(mock_msg.message,
                         mock_reduction_record.message)
        self.assertEqual(mock_msg.reduction_log,
                         mock_reduction_record.reduction_log)
        self.assertEqual(mock_msg.admin_log,
                         mock_reduction_record.admin_log)

        patched_db.save_record.assert_called_once_with(mock_reduction_record)

    def test_reduction_skipped_no_record(self, patched_db):
        """
        Tests reduction skipped raises if the reduction record is not in the db
        """
        self.handler.find_run = mock.Mock(return_value=None)
        with self.assertRaises(MissingReductionRunRecord):
            self.handler.reduction_skipped(message=self._get_mock_message())
        patched_db.save_record.assert_not_called()

    def test_reduction_error_no_retry(self, patched_db):
        """
        Tests reduction error handler when retry is not set
        """
        mock_reduction_record = mock.NonCallableMock()
        self.handler.find_run = mock.Mock(return_value=mock_reduction_record)

        mock_msg = self._get_mock_message()
        mock_msg.retry_in = None
        self.handler.reduction_error(message=mock_msg)
        self.assertEqual(self.mocked_utils.status.get_error(),
                         mock_reduction_record.status)
        self.assertEqual(mock_msg.message,
                         mock_reduction_record.message)
        self.assertEqual(mock_msg.reduction_log,
                         mock_reduction_record.reduction_log)
        self.assertEqual(mock_msg.admin_log,
                         mock_reduction_record.admin_log)

        patched_db.save_record.assert_called_once_with(mock_reduction_record)

    def test_reduction_error_missing_record(self, _):
        """
        Tests reduction error handler throws when a record is not in the db
        """
        self.handler.find_run = mock.Mock(return_value=None)
        with self.assertRaises(MissingReductionRunRecord):
            self.handler.reduction_error(message=self._get_mock_message())

    def test_reduction_error_retry_mechanism(self, patched_db):
        """
        Tests the reduction error method retries a set number of times
        before backing off.
        """
        mock_reduction_record = mock.NonCallableMock()
        self.handler.find_run = mock.Mock(return_value=mock_reduction_record)

        # Valid value *not* including 5
        for i in range(0, 5):
            mocked_msg = self._get_mock_message()
            self.handler._get_last_run_version = mock.Mock(return_value=i)
            self.handler.retry_run = mock.Mock()

            self.handler.reduction_error(message=mocked_msg)
            patched_db.get_experiment.assert_called_with(mocked_msg.rb_number)
            self.handler.retry_run.assert_called_once_with(
                mocked_msg.started_by, mock_reduction_record,
                mocked_msg.retry_in)

        # 5 and above should never retry
        for i in range(5, 7):
            mocked_msg = self._get_mock_message()
            self.handler.retry_run = mock.Mock()
            self.handler._get_last_run_version = mock.Mock(return_value=i)

            self.handler.reduction_error(mocked_msg)
            # As we are > limit the retry should be set to None
            self.assertIsNone(mocked_msg.retry_in)
            self.handler.retry_run.assert_not_called()

    def test_find_run(self, patched_db):
        """
        Tests fiind run makes the expected DB calls when invoked
        """
        mocked_msg = self._get_mock_message()
        mocked_msg.run_number = 100
        mocked_msg.run_version = 200
        mocked_experiment = mock.NonCallableMock()
        patched_db.get_experiment.return_value = mocked_experiment

        return_val = patched_db.start_database.return_value \
            .data_model.ReductionRun.objects \
            .filter.return_value \
            .filter.return_value \
            .filter.return_value \
            .first.return_value

        self.assertEqual(return_val, self.handler.find_run(message=mocked_msg))
        top_level_query = patched_db.start_database.return_value.data_model \
            .ReductionRun.objects
        top_level_query.filter \
            .assert_called_once_with(experiment_id=mocked_experiment.id)
        top_level_query.filter.return_value.filter \
            .assert_called_once_with(run_number=100)
        top_level_query.filter.return_value.filter.return_value.filter \
            .assert_called_once_with(run_version=200)

    def test_find_run_missing_experiment_record(self, patched_db):
        """
        Ensures find run will throw if the RB number passed does not
        exist
        """
        patched_db.get_experiment.return_value = None
        with self.assertRaises(MissingExperimentRecord):
            self.handler.find_run(self._get_mock_message())

    def test_retry_run(self, _):
        """
        Tests that retry run queues up the given message and sends
        it onwards to the queue client
        """
        reduction_run = mock.Mock()
        reduction_run.cancel = False

        mock_uid = mock.Mock()
        expected_time = 123

        self.handler.retry_run(user_id=mock_uid, retry_in=expected_time,
                               reduction_run=reduction_run)
        self.mocked_utils.reduction_run.create_retry_run\
            .assert_called_once_with(user_id=mock_uid, delay=expected_time,
                                     reduction_run=reduction_run)
        create_retry_run_ret = self.mocked_utils.reduction_run.create_retry_run()
        self.mocked_utils.messaging.send_pending.assert_called_once_with(
            create_retry_run_ret, delay=(expected_time * 1000))

    def test_retry_run_cancel(self, _):
        """
        Tests that retry run does not requeue up a cancelled message
        """
        reduction_run = mock.Mock()
        reduction_run.cancel = True
        self.assertIsNone(self.handler.retry_run(
            user_id=None, reduction_run=reduction_run, retry_in=None))
        self.mocked_utils.reduction_run.create_retry_run.assert_not_called()

    def test_construct_and_send_skipped(self, _):
        """
        Tests that the message contents is updated with the passed in msg
        then send onwards to the skipped queue
        """
        expected_msg = self._get_mock_message()
        self.handler._construct_and_send_skipped(
            rb_number=mock.NonCallableMock(),
            reason=mock.NonCallableMock(), message=expected_msg)

        self.mocked_client.send_message.assert_called_once_with(
            ACTIVEMQ_SETTINGS.reduction_skipped, expected_msg)


if __name__ == '__main__':
    unittest.main()
