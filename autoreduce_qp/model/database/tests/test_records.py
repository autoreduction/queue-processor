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
from unittest import TestCase, mock
import model.database.records as records


class TestDatabaseRecords(TestCase):
    """
    Tests the Record helpers for the ORM layer
    """
    @mock.patch("autoreduce_qp.model.database.records.timezone")
    def test_create_reduction_record_forwards_correctly(self, timezone_mock):
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
        mock_run_version = mock.NonCallableMock()
        mock_script_text = mock.NonCallableMock()
        mock_status = mock.NonCallableMock()

        with mock.patch("autoreduce_qp.model.database.records.ReductionRun") as reduction_run:
            returned = records.create_reduction_run_record(experiment=mock_experiment,
                                                           instrument=mock_inst,
                                                           message=mock_msg,
                                                           run_version=mock_run_version,
                                                           script_text=mock_script_text,
                                                           status=mock_status)

            self.assertEqual(reduction_run.return_value, returned)

            reduction_run.assert_called_once_with(
                run_number=mock_msg.run_number,
                run_version=mock_run_version,
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
