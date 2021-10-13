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
from autoreduce_db.reduction_viewer.models import DataLocation, Instrument, ReductionRun, RunNumber
from parameterized import parameterized
import autoreduce_qp.model.database.records as records
from queue_processor.tests.test_handle_message import FakeMessage, FakeModule

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

        _make_script_and_arguments.assert_called_once_with(mock_inst, mock_msg, False)
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

        load.return_value = FakeModule()
        msg = FakeMessage()
        msg.reduction_script = "print(123)"
        msg.reduction_arguments = None
        msg.rb_number = 123456
        instrument = Instrument.objects.first()

        expected_args = instrument.arguments.create(raw="{}", experiment_reference=msg.rb_number)
        # add arguments for a run range, just to make sure they don't get selected over the other ones
        instrument.arguments.create(raw="{}", start_run=msg.run_number)
        rscript, rargs = records._make_script_and_arguments(instrument, msg, False)

        assert rscript.text == "print(123)"
        assert rargs == expected_args

    @mock.patch("autoreduce_qp.model.database.records.ReductionScriptFile.load")
    def test_make_script_and_arguments_with_run_number_var(self, load: mock.Mock):
        """
        Test that the script is made, and arguments pre-configured to start from this run are selected.
        Also checks that older configurations are not picked over the latest one.
        """
        load.return_value = FakeModule()
        msg = FakeMessage()
        msg.reduction_script = "print(123)"
        msg.reduction_arguments = None
        msg.rb_number = 123456
        instrument = Instrument.objects.first()

        expected_args = instrument.arguments.create(raw="{}", start_run=msg.run_number)
        # add some more arguments that start earlier, to verify that only the latest one is selected
        instrument.arguments.create(raw="{}", start_run=msg.run_number - 1)
        instrument.arguments.create(raw="{}", start_run=msg.run_number - 2)
        rscript, rargs = records._make_script_and_arguments(instrument, msg, False)

        assert rscript.text == "print(123)"
        assert rargs == expected_args

        # reduction_arguments is None & not batch run
        # -> experiment vars - Done
        # -> start_run vars - Done
        # reduction_arguments is None & is batch run
        # reduction_arguments not None & does not exist
        # reduction_arguments not None & exists
