# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
"""
Unit tests for the record helper module
"""

import socket
from typing import List, Union
from unittest import mock
from django.test import TestCase
from autoreduce_db.reduction_viewer.models import DataLocation, Experiment, Instrument, ReductionRun, RunNumber
from parameterized import parameterized

from autoreduce_qp.model.database import records
from autoreduce_qp.queue_processor.tests.test_handle_message import make_test_message, FakeModule

# pylint:disable=no-member


class TestDatabaseRecords(TestCase):
    """
    Tests the Record helpers for the ORM layer
    """
    fixtures = ["status_fixture", "run_with_multiple_variables"]

    # pylint:disable=invalid-name
    @mock.patch("autoreduce_qp.model.database.records.timezone")
    @mock.patch.multiple("autoreduce_qp.model.database.records",
                         ReductionRun=mock.DEFAULT,
                         _make_run_numbers=mock.DEFAULT,
                         _make_data_locations=mock.DEFAULT,
                         _make_script_and_arguments=mock.DEFAULT)
    def test_create_reduction_record_forwards_correctly(self, timezone_mock, ReductionRun: mock.Mock,
                                                        _make_run_numbers: mock.Mock, _make_data_locations: mock.Mock,
                                                        _make_script_and_arguments: mock.Mock):
        """
        Test: Reduction Record uses args correctly.
        Any fields which are hard-coded are mocked with ANY to prevent
        this test becoming brittle to future change. If we expect a user
        to pass them in as an arg we should test they get unpacked correctly

        When: Called to simplify ORM record creation
        """
        mock_experiment = mock.NonCallableMock()
        mock_inst = mock.NonCallableMock()
        mock_msg = mock.NonCallableMock()
        mock_msg.run_number = 12345
        mock_run_version = mock.NonCallableMock()
        mock_script = mock.NonCallableMock()
        mock_arguments = mock.NonCallableMock()
        mock_status = mock.NonCallableMock()

        _make_script_and_arguments.return_value = (mock_script, mock_arguments)

        returned_run, returned_msg = records.create_reduction_run_record(experiment=mock_experiment,
                                                                         instrument=mock_inst,
                                                                         message=mock_msg,
                                                                         run_version=mock_run_version,
                                                                         status=mock_status)

        self.assertEqual(ReductionRun.objects.create.return_value, returned_run)
        self.assertEqual(mock_msg, returned_msg)

        _make_script_and_arguments.assert_called_once_with(mock_experiment, mock_inst, mock_msg, False)
        ReductionRun.objects.create.assert_called_once_with(
            run_version=mock_run_version,
            batch_run=False,
            created=timezone_mock.now.return_value,
            last_updated=timezone_mock.now.return_value,
            experiment=mock_experiment,
            instrument=mock_inst,
            status_id=mock_status.id,
            started_by=mock_msg.started_by,
            # Hardcoded below
            run_description=mock.ANY,
            hidden_in_failviewer=mock.ANY,
            admin_log=mock.ANY,
            reduction_log=mock.ANY,
            reduction_host=socket.getfqdn(),
            script=mock_script,
            arguments=mock_arguments)

        _make_run_numbers.assert_called_once_with(returned_run, mock_msg.run_number)
        _make_data_locations.assert_called_once_with(returned_run, mock_msg.data)

    @parameterized.expand([["/test/data/loc"], [["/test/data/loc/", "/test/data/loc2"]]])
    def test_make_data_locations(self, data_locs: Union[str, List[str]]):
        """Test that make_data_locations supports both a string and a list,
        and creates the database objects correctly."""
        assert DataLocation.objects.count() == 0
        reduction_run = ReductionRun.objects.first()
        records._make_data_locations(reduction_run, data_locs)

        if not isinstance(data_locs, list):
            assert DataLocation.objects.count() == 1
        else:
            assert DataLocation.objects.count() == len(data_locs)

    @parameterized.expand([[123456], [[123456, 1234567]]])
    def test_make_run_numbers(self, run_numbers: Union[int, List[int]]):
        """Test that make_run_numbers supports both a string and a list,
        and creates the database objects correctly."""
        assert RunNumber.objects.count() == 1  # 1 comes from the fixture
        reduction_run = ReductionRun.objects.first()
        records._make_run_numbers(reduction_run, run_numbers)

        if not isinstance(run_numbers, list):
            assert RunNumber.objects.count() == 2
        else:
            assert RunNumber.objects.count() == len(run_numbers) + 1

    @mock.patch("autoreduce_qp.model.database.records.ReductionScriptFile.load")
    def test_make_script_and_arguments_with_experiment_var(self, load: mock.Mock):
        """
        Test that the script is made, and the arguments selected are
        the ones with a set experiment variable, as they are TOP priority over other variables.
        """

        instrument: Instrument = Instrument.objects.first()
        experiment: Experiment = Experiment.objects.first()

        load.return_value = FakeModule()
        msg = make_test_message(instrument.name)
        msg.reduction_script = "print(123)"
        msg.reduction_arguments = None
        msg.rb_number = experiment.reference_number

        expected_args = instrument.arguments.create(raw="{}", experiment_reference=experiment.reference_number)
        # add arguments for a run range, just to make sure they don't get selected over the other ones
        instrument.arguments.create(raw="{}", start_run=msg.run_number)
        rscript, rargs = records._make_script_and_arguments(experiment, instrument, msg, False)

        assert rscript.text == "print(123)"
        assert rargs == expected_args

    @mock.patch("autoreduce_qp.model.database.records.ReductionScriptFile.load")
    def test_make_script_and_arguments_with_run_number_var(self, load: mock.Mock):
        """
        Test that the script is made, and arguments pre-configured to start from this run are selected.
        Also checks that older configurations are not picked over the latest one.
        """
        instrument: Instrument = Instrument.objects.first()
        experiment: Experiment = Experiment.objects.first()

        load.return_value = FakeModule()
        msg = make_test_message(instrument.name)
        msg.reduction_script = "print(123)"
        msg.reduction_arguments = None
        msg.rb_number = experiment.reference_number

        expected_args = instrument.arguments.create(raw="{}", start_run=msg.run_number)
        # add some more arguments that start earlier, to verify that only the latest one is selected
        instrument.arguments.create(raw="{}", start_run=msg.run_number - 1)
        instrument.arguments.create(raw="{}", start_run=msg.run_number - 2)
        rscript, rargs = records._make_script_and_arguments(experiment, instrument, msg, False)

        assert rscript.text == "print(123)"
        assert rargs == expected_args

    @mock.patch("autoreduce_qp.model.database.records.ReductionScriptFile.load")
    def test_make_script_and_arguments_repeat_runs(self, load: mock.Mock):
        """
        Test that the script is made, and arguments from the message.reduction_arguments
        are picked over ALL others. This is used for reruns, and in that case a user would
        expect that the arguments they re-ran with, take precedence over any others.

        This test checks the case when the message.reduction_arguments do not match any
        in the database.
        """
        instrument: Instrument = Instrument.objects.first()
        experiment: Experiment = Experiment.objects.first()

        load.return_value = FakeModule()
        msg = make_test_message(instrument.name)
        msg.reduction_script = "print(123)"
        msg.reduction_arguments = None
        msg.rb_number = 123456

        rscript, rargs = records._make_script_and_arguments(experiment, instrument, msg, False)

        assert rscript.text == "print(123)"
        # running it again should `get` the first object return the same DB record
        rscript_second_run, rargs_second_run = records._make_script_and_arguments(experiment, instrument, msg, False)

        assert rscript == rscript_second_run
        assert rargs == rargs_second_run

    @mock.patch("autoreduce_qp.model.database.records.ReductionScriptFile.load")
    def test_make_script_and_arguments_args_from_message(self, load: mock.Mock):
        """
        Test that the script is made, and arguments from the message.reduction_arguments
        are picked over ALL others. This is used for reruns, and in that case a user would
        expect that the arguments they re-ran with, take precedence over any others.

        This test checks the case when the message.reduction_arguments do not match any
        in the database.
        """
        instrument: Instrument = Instrument.objects.first()
        experiment: Experiment = Experiment.objects.first()

        load.return_value = FakeModule()
        msg = make_test_message(instrument.name)
        msg.reduction_script = "print(123)"
        msg.reduction_arguments = {"standard_vars": {"variable": "value"}}
        msg.rb_number = 123456

        expected_args = instrument.arguments.create(raw="{}", start_run=msg.run_number)
        rscript, rargs = records._make_script_and_arguments(experiment, instrument, msg, False)

        load.assert_not_called()

        assert rscript.text == "print(123)"
        # args were passed in with the message, so they would not equal the ones we have made
        assert rargs != expected_args
        # but running it again should `get` the first object return the same DB record
        rscript_second_run, rargs_second_run = records._make_script_and_arguments(experiment, instrument, msg, False)

        assert rscript == rscript_second_run
        assert rargs == rargs_second_run

    @parameterized.expand([[{"experiment_reference": 7272727}], [{"start_run": 1237474}]])
    @mock.patch("autoreduce_qp.model.database.records.ReductionScriptFile.load")
    def test_make_script_and_arguments_args_from_message_will_not_reuse_matching_exp_or_run_args(
            self, create_args: dict, load: mock.Mock):
        """
        Test that the script is made, and arguments from the message.reduction_arguments
        are picked over ALL others. This is used for reruns, and in that case a user would
        expect that the arguments they re-ran with, take precedence over any others.

        This test checks the case when the message.reduction_arguments
        matches some other object in the database, it will not reuse
        them if they have a value for start_run or experiment_reference.
        """
        instrument: Instrument = Instrument.objects.first()
        experiment: Experiment = Experiment.objects.first()

        load.return_value = FakeModule()
        msg = make_test_message(instrument.name)
        msg.reduction_script = "print(123)"
        msg.reduction_arguments = {"standard_vars": {"variable": "value"}}
        msg.rb_number = 123456

        expected_args = instrument.arguments.create(raw='{"standard_vars":{"variable":"value"}}', **create_args)
        rscript, rargs = records._make_script_and_arguments(experiment, instrument, msg, False)

        load.assert_not_called()

        assert rscript.text == "print(123)"
        # args were passed in with the message, but they happen to match previous ones in the DB
        # so the object should be re-used
        assert rargs != expected_args

    @mock.patch("autoreduce_qp.model.database.records.ReductionScriptFile.text")
    def test_make_script_and_arguments_load_script(self, text: mock.Mock):
        """
        Test that the script is made, and arguments from the message.reduction_arguments
        are picked over ALL others. This is used for reruns, and in that case a user would
        expect that the arguments they re-ran with, take precedence over any others.

        This test checks the case when the message.reduction_arguments do not match any
        in the database.
        """
        instrument: Instrument = Instrument.objects.first()
        experiment: Experiment = Experiment.objects.first()
        text.return_value = "test script value"

        msg = make_test_message(instrument.name)
        msg.reduction_script = None
        msg.reduction_arguments = {"standard_vars": {"variable": "value"}}
        msg.rb_number = 123456

        rscript, _ = records._make_script_and_arguments(experiment, instrument, msg, False)

        assert rscript.text == text.return_value
