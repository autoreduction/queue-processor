# ############################################################################### #
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the queue processor
"""
# We need to mock out ._foo methods so disable warning
# pylint: disable=protected-access
# pylint: disable=missing-function-docstring
# pylint: disable=fixme

import unittest
from unittest import mock

from mock import patch, MagicMock, Mock

from model.message.job import Message
from queue_processors.queue_processor import listener
from queue_processors.queue_processor.listener import Listener, \
    _UtilsClasses
from utils.clients.queue_client import QueueClient
from utils.clients.settings.client_settings_factory import ActiveMQSettings


class TestQueueProcessor(unittest.TestCase):
    """
    Exercises the functions within listener.py
    """

    def setUp(self):
        self.test_consumer_name = "Test_Autoreduction_QueueProcessor"

    @patch('utils.clients.queue_client.QueueClient.__init__',
           return_value=None)
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.subscribe_autoreduce')
    def test_setup_connection(self, mock_sub_ar, mock_connect, mock_client):
        """
        Test: Connection to ActiveMQ setup, along with subscription to queues
        When: setup_connection is called with a consumer name
        """
        listener.setup_connection(self.test_consumer_name)

        mock_client.assert_called_once()
        mock_connect.assert_called_once()
        mock_sub_ar.assert_called_once()

        (args, _) = mock_sub_ar.call_args
        self.assertEqual(args[0], self.test_consumer_name)
        self.assertIsInstance(args[1], Listener)
        self.assertIsInstance(args[1]._client, QueueClient)


class TestUtilsClasses(unittest.TestCase):
    """
    Tests the _Utils class
    """
    def test_default_constructable(self):
        self.assertIsNotNone(_UtilsClasses())


@patch("queue_processors.queue_processor.listener.db_access")
class TestListener(unittest.TestCase):
    # We have too many public methods as our Class Under Test does too much...
    # pylint: disable=too-many-public-methods
    """
    Exercises the Listener
    """

    def setUp(self):
        self.mocked_client = mock.Mock()
        self.mocked_logger = mock.Mock()
        self.mocked_def_message = mock.Mock(spec=Message())
        # Magic for [] operator
        self.mocked_utils = mock.MagicMock(spec=_UtilsClasses())

        self.listener = Listener(client=self.mocked_client)
        self.listener.message = self.mocked_def_message
        self.listener._logger = self.mocked_logger
        self.listener._utils = self.mocked_utils

    @staticmethod
    def _get_header(destination=None):
        if destination is None:
            destination = mock.NonCallableMock()

        return {"destination": destination,
                "priority": mock.NonCallableMock()}

    def test_construct_and_send_skipped(self, _):
        """
        Test: The message is sent via the QueueClient with a populated
        message attribute
        When: _construct_and_send_skipped is called
        """
        mock_client = MagicMock(name="QueueClient")
        listener = Listener(mock_client)
        test_rb_number = 1
        test_reason = "test"
        listener._construct_and_send_skipped(test_rb_number, test_reason)

        self.assertIsNotNone(listener.message)

        mocked_init = Mock()
        expected_msg = ActiveMQSettings(host=mocked_init, port=mocked_init,
                                        username=mocked_init,
                                        password=mocked_init).reduction_skipped

        mock_client.send.assert_called_once_with(expected_msg,
                                                 listener.message,
                                                 priority=listener._priority)
        sent_message = mock_client.send.call_args[0][1]
        self.assertEqual(sent_message, listener.message)

    def test_on_message_stores_priority(self, _):
        headers = self._get_header()
        self.listener.on_message(headers=headers, message=Message())
        self.assertEqual(headers["priority"], self.listener._priority)

    def test_on_message_with_message_type(self, _):
        msg = Message()
        self.assertIsNone(self.listener.on_message(headers=self._get_header(),
                                                   message=msg))

        self.assertEqual(msg, self.listener.message)

    def test_on_message_with_non_message(self, _):
        # Patch out the populate method as we assume is tested elsewhere
        non_msg = "Some JSON String"
        self.listener.on_message(headers=self._get_header(),
                                 message=non_msg)

        self.mocked_def_message.populate.assert_called_once_with(non_msg)

    def test_on_message_handles_throw(self, _):
        self.listener.message = Mock()
        self.listener.message.populate.side_effect = ValueError()

        self.listener.on_message(headers=self._get_header(), message="")
        self.mocked_logger.error.assert_called()

    def test_on_message_sends_to_correct_queue(self, _):
        listener = self.listener  # Reduce typing self.listener each time
        listener.data_ready = Mock()
        listener.reduction_started = Mock()
        listener.reduction_complete = Mock()
        listener.reduction_error = Mock()
        listener.reduction_skipped = Mock()

        # queue_name -> method
        to_test = {"/queue/DataReady": listener.data_ready,
                   "/queue/ReductionStarted": listener.reduction_started,
                   "/queue/ReductionComplete": listener.reduction_complete,
                   "/queue/ReductionError": listener.reduction_error,
                   "/queue/ReductionSkipped": listener.reduction_skipped,
                   "unknown": self.mocked_logger.warning}

        for name, method in to_test.items():
            # Ensure something else didn't accidentally call the method
            method.assert_not_called()
            self.listener.on_message(headers=self._get_header(name),
                                     message="")
            method.assert_called_once()

    def test_on_message_exception(self, _):
        # Pretend reduction_error throws if something dire is wrong
        self.listener.reduction_error = Mock()
        self.listener.reduction_error.side_effect = RuntimeError()

        self.listener.on_message(
            headers=self._get_header("/queue/ReductionError"), message="")

        self.mocked_logger.error.assert_called()

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
                ".order_by.return_value"
                ".first.return_value": mock_existing_reduction_run}

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

        self.listener.data_ready()
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

            self.listener.data_ready()

            # TODO we are def passing too much in here
            mock_reduction_constructor.assert_called_once_with(
                run_name='', cancel=0, hidden_in_failviewer=0,
                admin_log='', reduction_log='',
                created=mock.ANY, last_updated=mock.ANY,
                run_version=expected_vers,
                # Mocked inputs below
                run_number=self.mocked_def_message.run_number,
                experiment_id=mock_experiment.id,
                instrument_id=mock_instrument.id,
                status_id=self.mocked_utils.status.get_skipped().id,
                script=self.mocked_utils.instrument_variable
                .get_current_script_text()[0],
                started_by=self.mocked_def_message.started_by)

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

        self.mocked_client.send.assert_not_called()

    def test_data_ready_empty_script_calls_error(self, patched_db):
        patched_db.configure_mock(**self._get_mocked_db_return_vals(
            mock_data_location=mock.Mock(),
            mock_new_reduction_run=mock.Mock(),
            mock_existing_reduction_run=None,
            mock_instrument=mock.Mock()))

        self.listener.reduction_error = mock.Mock()
        self.mocked_utils.instrument_variable\
            .get_current_script_text.return_value = [None]

        self.listener.data_ready()
        self.listener.reduction_error.assert_called_once()

    @patch("queue_processors.queue_processor.listener.is_valid_rb")
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
        self.listener.data_ready()

        # Assert Database accesses
        patched_db.get_instrument.assert_called_with(
            str(self.mocked_def_message.instrument), create=True)
        patched_db.get_experiment.assert_called_with(
            self.mocked_def_message.rb_number, create=True)
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
        self.assertEqual(mock_reduction_run.run_version,
                         self.mocked_def_message.run_version)
        self.assertEqual(mock_script_and_args[0],
                         self.mocked_def_message.reduction_script)
        self.assertEqual(mock_script_and_args[1],
                         self.mocked_def_message.reduction_arguments)

        # Finally check if the data is sent
        self.mocked_client.send.assert_called_once_with(
            "/queue/ReductionPending", self.mocked_def_message,
            priority=self.listener._priority)

    def test_reduction_started(self, patched_db):
        mock_reduction_record = mock.NonCallableMock()
        self.listener.find_run = mock.Mock(return_value=mock_reduction_record)

        valid_states = ["Error", "Queued"]
        for state in valid_states:
            mock_reduction_record.status.value = state
            self.listener.reduction_started()

            self.mocked_utils.status.get_processing.assert_called_once()
            self.assertEqual(self.mocked_utils.status.get_processing(),
                             mock_reduction_record.status)
            patched_db.save_record.called_once_with(mock_reduction_record)

            self.mocked_utils.status.get_processing.reset_mock()
            patched_db.save_record.reset_mock()

        # Failure case should do very little
        mock_reduction_record.status.value = "Unknown"
        self.listener.reduction_started()

        self.mocked_logger.error.assert_called()
        self.mocked_utils.status.get_processing.assert_not_called()
        patched_db.save_record.assert_not_called()

    def test_reduction_complete(self, patched_db):
        self.mocked_def_message.reduction_data = None
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Processing"
        self.listener.find_run = mock.Mock(return_value=mock_reduction_record)

        self.listener.reduction_complete()

        self.assertEqual(self.mocked_utils.status.get_completed(),
                         mock_reduction_record.status)
        self.assertEqual(self.mocked_def_message.message,
                         mock_reduction_record.message)
        self.assertEqual(self.mocked_def_message.reduction_log,
                         mock_reduction_record.reduction_log)
        self.assertEqual(self.mocked_def_message.admin_log,
                         mock_reduction_record.admin_log)

        patched_db.save_record.assert_called_once_with(mock_reduction_record)

    def test_reduction_complete_saves_location_records(self, patched_db):
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Processing"
        self.listener.find_run = mock.Mock(return_value=mock_reduction_record)

        location_records = [mock.NonCallableMock(), mock.NonCallableMock()]
        self.mocked_def_message.reduction_data = location_records

        mocked_reduction_location = mock.NonCallableMock()
        patched_db.start_database.return_value.data_model.\
            ReductionLocation.return_value = mocked_reduction_location

        self.listener.reduction_complete()
        patched_db.save_record.assert_any_call(mocked_reduction_location)
        # n - Location records, +1 for Reduction Run Record
        self.assertEqual(len(location_records) + 1,
                         patched_db.save_record.call_count)

    def test_reduction_complete_with_invalid_state(self, patched_db):
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Unknown"
        self.listener.find_run = mock.Mock(return_value=mock_reduction_record)

        self.listener.reduction_complete()
        self.mocked_logger.error.assert_called()
        patched_db.save_record.assert_not_called()

    def test_reduction_skipped(self, patched_db):
        mock_reduction_record = mock.NonCallableMock()
        mock_reduction_record.status.value = "Processing"
        self.listener.find_run = mock.Mock(return_value=mock_reduction_record)

        self.listener.reduction_skipped()
        self.assertEqual(self.mocked_utils.status.get_skipped(),
                         mock_reduction_record.status)
        self.assertEqual(self.mocked_def_message.message,
                         mock_reduction_record.message)
        self.assertEqual(self.mocked_def_message.reduction_log,
                         mock_reduction_record.reduction_log)
        self.assertEqual(self.mocked_def_message.admin_log,
                         mock_reduction_record.admin_log)

        patched_db.save_record.assert_called_once_with(mock_reduction_record)

    def test_reduction_skipped_no_record(self, patched_db):
        self.listener.find_run = mock.Mock(return_value=None)
        self.listener.reduction_skipped()
        self.mocked_logger.error.assert_called()
        patched_db.save_record.assert_not_called()

    def test_reduction_error_no_retry(self, patched_db):
        mock_reduction_record = mock.NonCallableMock()
        self.listener.find_run = mock.Mock(return_value=mock_reduction_record)
        self.mocked_def_message.retry_in = None

        self.listener.reduction_error()
        self.assertEqual(self.mocked_utils.status.get_error(),
                         mock_reduction_record.status)
        self.assertEqual(self.mocked_def_message.message,
                         mock_reduction_record.message)
        self.assertEqual(self.mocked_def_message.reduction_log,
                         mock_reduction_record.reduction_log)
        self.assertEqual(self.mocked_def_message.admin_log,
                         mock_reduction_record.admin_log)

        patched_db.save_record.assert_called_once_with(mock_reduction_record)

    def test_reduction_error_retry_mechanism(self, patched_db):
        mock_existing_reduction_run = mock.Mock()
        mock_reduction_record = mock.NonCallableMock()
        self.listener.find_run = mock.Mock(return_value=mock_reduction_record)
        self.listener.retry_run = mock.Mock()

        # TODO this should use ORDER-BY and LIMIT 1
        patched_db.start_database.return_value.data_model\
            .ReductionRun\
            .filter.return_value\
            .filter.return_value = [mock_existing_reduction_run]

        # Valid value *not* including 5
        for i in range(0, 5):
            mock_existing_reduction_run.run_version = i
            self.listener.reduction_error()
            patched_db.get_experiment\
                .assert_called_with(self.mocked_def_message.rb_number)
            self.listener.retry_run.assert_called_once_with\
                (self.mocked_def_message.started_by, mock_reduction_record,
                 self.mocked_def_message.retry_in)
            self.listener.retry_run.reset_mock()

        # 5 and above should never retry
        for i in range(5, 7):
            mock_existing_reduction_run.run_version = i
            self.mocked_def_message.retry_in = mock.NonCallableMock()
            self.listener.reduction_error()
            self.assertIsNone(self.mocked_def_message.retry_in)
            self.listener.retry_run.assert_not_called()

    def test_find_run(self, patched_db):
        self.mocked_def_message.run_number = 100
        self.mocked_def_message.run_version = 200
        mocked_experiment = mock.NonCallableMock()
        patched_db.get_experiment.return_value = mocked_experiment

        return_val = patched_db.start_database.return_value \
            .data_model.ReductionRun.objects \
            .filter.return_value \
            .filter.return_value \
            .filter.return_value \
            .first.return_value

        self.assertEqual(return_val, self.listener.find_run())
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

        self.listener.retry_run(user_id=mock_uid, retry_in=expected_time,
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
        self.assertIsNone(self.listener.retry_run(
            user_id=None, reduction_run=reduction_run, retry_in=None))
        self.mocked_utils.reduction_run.create_retry_run.assert_not_called()


class TestQueueProcessorFreeFuncs(unittest.TestCase):
    """
    Tests the free functions in Queue Processor
    """
    def test_is_valid_rb(self):
        valid_values = [1, 20, "10000"]
        for i in valid_values:
            self.assertIsNone(listener.is_valid_rb(i))

        invalid_values = [0, 0.1, -1, -100, None, "foo"]
        for i in invalid_values:
            self.assertIsInstance(listener.is_valid_rb(i), str)
