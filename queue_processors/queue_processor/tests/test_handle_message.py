# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
import unittest
from unittest import mock
from unittest.mock import patch

from model.message.job import Message
from queue_processors.queue_processor import handle_message
from queue_processors.queue_processor._utils_classes import _UtilsClasses
from queue_processors.queue_processor.handle_message import HandleMessage
from queue_processors.queue_processor.stomp_client import StompClient


class TestHandleMessageFreeFuncs(unittest.TestCase):
    """
    Tests the free functions in Queue Processor
    """
    def test_is_valid_rb(self):
        valid_values = [1, 20, "10000"]
        for i in valid_values:
            self.assertIsNone(handle_message.is_valid_rb(i))

        invalid_values = [0, 0.1, -1, -100, None, "foo"]
        for i in invalid_values:
            self.assertIsInstance(handle_message.is_valid_rb(i), str)


@patch("queue_processors.queue_processor.handle_message.db_access")
class TestHandleMessage(unittest.TestCase):

    @patch("queue_processors.queue_processor.handle_message._UtilsClasses")
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
        return mock.Mock(spec=Message())

    def test_data_model_only_inits_once(self, patched_db):
        model_mock = patched_db.start_database.return_value.data_model
        first_call = self.handler._data_model
        patched_db.start_database.assert_called_once()
        self.assertEqual(model_mock, first_call)

        patched_db.start_database.reset_mock()
        second_call = self.handler._data_model
        patched_db.start_database.assert_not_called()
        self.assertEqual(first_call, second_call)

    def test_data_ready_marks_inst_active(self, patched_db):
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

            mock_message =self._get_mock_message()
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
        patched_db.configure_mock(**self._get_mocked_db_return_vals(
            mock_data_location=mock.Mock(),
            mock_new_reduction_run=mock.Mock(),
            mock_existing_reduction_run=None,
            mock_instrument=mock.Mock()))

        self.handler.reduction_error = mock.Mock()
        self.mocked_utils.instrument_variable\
            .get_current_script_text.return_value = [None]

        self.handler.data_ready(self._get_mock_message())
        self.handler.reduction_error.assert_called_once()

    @patch("queue_processors.queue_processor.handle_message.is_valid_rb")
    def test_data_ready_with_new_data(self, valid_rb, patched_db):
        # This is the "ideal" flow hence it's the largest and
        # should be split down
        mock_instrument = mock.NonCallableMock()
        mock_instrument.is_active = True
        mock_instrument.is_paused = False

        mock_data_location = mock.NonCallableMock()
        mock_reduction_run = mock.NonCallableMock()
        mock_script_and_args = (mock.NonCallableMock(), mock.NonCallableMock())

        self.mocked_utils.reduction_run. \
            get_script_and_arguments.return_value = mock_script_and_args
        valid_rb.return_value = None  # None means valid (?)

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

        # Failure case should do very little
        mock_reduction_record.status.value = "Unknown"
        self.handler.reduction_started(message=self._get_mock_message())

        self.mocked_logger.error.assert_called()
        self.mocked_utils.status.get_processing.assert_not_called()
        patched_db.save_record.assert_not_called()

    def test_reduction_complete(self, patched_db):
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
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Unknown"
        self.handler.find_run = mock.Mock(return_value=mock_reduction_record)

        mocked_msg = self._get_mock_message()
        self.handler.reduction_complete(message=mocked_msg)
        self.mocked_logger.error.assert_called()
        patched_db.save_record.assert_not_called()

    def test_reduction_skipped(self, patched_db):
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
        self.handler.find_run = mock.Mock(return_value=None)
        self.handler.reduction_skipped(message=self._get_mock_message())
        self.mocked_logger.error.assert_called()
        patched_db.save_record.assert_not_called()

    def test_reduction_error_no_retry(self, patched_db):
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

    def test_reduction_error_retry_mechanism(self, patched_db):
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

    def test_retry_run(self, _):
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
        reduction_run = mock.Mock()
        reduction_run.cancel = True
        self.assertIsNone(self.handler.retry_run(
            user_id=None, reduction_run=reduction_run, retry_in=None))
        self.mocked_utils.reduction_run.create_retry_run.assert_not_called()



if __name__ == '__main__':
    unittest.main()
