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

from unittest import TestCase, mock
import model.database.records as records


class TestDatabaseRecords(TestCase):
    """
    Tests the Record helpers for the ORM layer
    """
    @staticmethod
    @mock.patch("model.database.access")
    def test_create_reduction_record_starts_db(db_layer):
        """
        Test: The correct DB accesses are made
        When: Creating the reduction record
        """
        # We do not actually care about what was passed in for this test
        arg = mock.NonCallableMock()
        records.create_reduction_run_record(arg, arg, arg, arg, arg, arg)

        db_layer.start_database.assert_called_once()
        db_layer.start_database.return_value.data_model\
            .ReductionRun.assert_called_once()

    @mock.patch("model.database.access")
    @mock.patch("datetime.datetime")
    def test_create_reduction_record_forwards_correctly(self, datetime_patch, db_layer):
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

        returned = records.create_reduction_run_record(experiment=mock_experiment,
                                                       instrument=mock_inst,
                                                       message=mock_msg,
                                                       run_version=mock_run_version,
                                                       script_text=mock_script_text,
                                                       status=mock_status)

        mock_record_orm = db_layer.start_database.return_value.data_model

        self.assertEqual(mock_record_orm.ReductionRun.return_value, returned)

        mock_record_orm.ReductionRun.assert_called_once_with(
            run_number=mock_msg.run_number,
            run_version=mock_run_version,
            created=datetime_patch.utcnow.return_value,
            last_updated=datetime_patch.utcnow.return_value,
            experiment=mock_experiment,
            instrument=mock_inst,
            status_id=mock_status.id,
            script=mock_script_text,
            started_by=mock_msg.started_by,
            # Hardcoded below
            run_description=mock.ANY,
            hidden_in_failviewer=mock.ANY,
            admin_log=mock.ANY,
            reduction_log=mock.ANY)
