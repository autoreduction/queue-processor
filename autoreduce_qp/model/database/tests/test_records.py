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
from autoreduce_db.reduction_viewer.models import DataLocation, ReductionRun, RunNumber
from parameterized import parameterized
import autoreduce_qp.model.database.records as records


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
                         _make_data_locations=mock.DEFAULT)
    def test_create_reduction_record_forwards_correctly(self, timezone_mock, ReductionRun: mock.Mock,
                                                        _make_run_numbers: mock.Mock, _make_data_locations: mock.Mock):
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
        mock_script_text = mock.NonCallableMock()
        mock_status = mock.NonCallableMock()

        returned = records.create_reduction_run_record(experiment=mock_experiment,
                                                       instrument=mock_inst,
                                                       message=mock_msg,
                                                       run_version=mock_run_version,
                                                       script_text=mock_script_text,
                                                       status=mock_status)

        self.assertEqual(ReductionRun.objects.create.return_value, returned)

        ReductionRun.objects.create.assert_called_once_with(
            run_version=mock_run_version,
            batch_run=False,
            created=timezone_mock.now.return_value,
            last_updated=timezone_mock.now.return_value,
            experiment=mock_experiment,
            instrument=mock_inst,
            status_id=mock_status.id,
            script=mock_script_text,
            started_by=mock_msg.started_by,
            # Hardcoded below
            run_description=mock.ANY,
            hidden_in_failviewer=mock.ANY,
            admin_log=mock.ANY,
            reduction_log=mock.ANY,
            reduction_host=socket.getfqdn())

        _make_run_numbers.assert_called_once_with(returned, mock_msg.run_number)
        _make_data_locations.assert_called_once_with(returned, mock_msg.data)

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
        assert RunNumber.objects.count() == 0
        reduction_run = ReductionRun.objects.first()
        records._make_run_numbers(reduction_run, run_numbers)

        if not isinstance(run_numbers, list):
            assert RunNumber.objects.count() == 1
        else:
            assert RunNumber.objects.count() == len(run_numbers)
