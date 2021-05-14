# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests to exercise the code responsible for common database access methods
"""
import unittest

from unittest.mock import patch, Mock

from model.database import access
from model.database.access import get_all_instrument_names, is_instrument_flat_output
from model.database.records import create_reduction_run_record
from queue_processors.queue_processor.tests.test_handle_message import FakeMessage


# pylint:disable=no-member
class TestAccess(unittest.TestCase):
    """
    Test the access functionality for the database
    """
    def setUp(self) -> None:
        self.database = access.start_database()

    # pylint:disable=no-self-use
    @patch('model.database.access.DatabaseClient.connect')
    def test_start_database(self, mock_connect):
        """
        Test: The database is initialised
        When:  start_database is called
        """
        access.start_database()
        mock_connect.assert_called_once()

    def test_get_instrument_valid(self):
        """
        Test: The correct instrument object is returned
        When: get_instrument is called on a valid database connection
        """
        actual = access.get_instrument('GEM')
        self.assertIsNotNone(actual)
        self.assertEqual('GEM', actual.name)

    def test_get_all_instrument_names(self):
        """
        Test: Correct instument names returned
        """
        instrument, _ = self.database.data_model.Instrument.objects.get_or_create(name="ARMI", is_active=1, is_paused=0)

        self.assertEqual(["ARMI"], get_all_instrument_names())

        instrument.delete()

    def test_is_instrument_flat_output(self):
        """
        Test: returns true for flat, False otherwise
        """
        flat_instrument, _ = self.database.data_model.Instrument.objects.get_or_create(name="flat_instrument",
                                                                                       is_active=1,
                                                                                       is_paused=0,
                                                                                       is_flat_output=1)

        non_flat_instrument, _ = self.database.data_model.Instrument.objects.get_or_create(name="non_flat_instrument",
                                                                                           is_active=1,
                                                                                           is_paused=1,
                                                                                           is_flat_output=0)

        self.assertTrue(is_instrument_flat_output("flat_instrument"))
        self.assertFalse(is_instrument_flat_output("non_flat_instrument"))

        flat_instrument.delete()
        non_flat_instrument.delete()

    def test_get_status(self):
        """
        Test: The correct Status record is returned
        When: get_status is called on a database containing the expected Status value
        """
        actual = access.get_status('c')
        self.assertIsNotNone(actual)
        self.assertEqual('Completed', actual.value_verbose())

    def test_get_experiment(self):
        """
        Test: The correct Experiment record is returned
        When: get_status is called on a database containing expected Experiment reference number
        """
        actual = access.get_experiment('123')
        self.assertIsNotNone(actual)
        self.assertEqual(str(123), str(actual.reference_number))

    def test_get_experiment_create(self):
        """
        Test: An Experiment record is created
        When: get_experiment is called with create option True
        """
        actual = access.get_experiment(rb_number=9999999)
        self.assertIsInstance(actual, self.database.data_model.Experiment)
        actual.delete()

    def test_get_software(self):
        """
        Test: The correct Software record is returned
        When: get_software is called with values that match a database record
        """
        actual = access.get_software('Mantid', '4.0')
        self.assertIsNotNone(actual)
        self.assertEqual('Mantid', actual.name)
        self.assertEqual('4.0', actual.version)
        actual.delete()

    # pylint:disable=no-self-use
    def test_get_reduction_run_valid(self):
        """
        Test: A ReductionRun record is returned
        When: get_reduction_run is called with values that match a database record
        """
        experiment, _ = self.database.data_model.Experiment.objects.get_or_create(reference_number=1231231)
        instrument, _ = self.database.data_model.Instrument.objects.get_or_create(name="ARMI", is_active=1, is_paused=0)
        status = access.get_status("q")
        fake_script_text = "scripttext"
        reduction_run = create_reduction_run_record(experiment, instrument, FakeMessage(), 0, fake_script_text, status)
        reduction_run.save()

        assert access.get_reduction_run('ARMI', 1234567).first() == reduction_run

        reduction_run.delete()
        experiment.delete()
        instrument.delete()

    def test_get_reduction_run_invalid(self):
        """
        Test: None is returned
        When: get_reduction_run is called values not in the database
        """
        actual = access.get_reduction_run('GEM', 0)
        self.assertIsNone(actual.first())

    def test_find_highest_run_version(self):
        """
        Test: The expected highest version number is returned
        When: Calling find_highest_run_version
        """

        experiment, _ = self.database.data_model.Experiment.objects.get_or_create(reference_number=1231231)
        instrument, _ = self.database.data_model.Instrument.objects.get_or_create(name="ARMI", is_active=1, is_paused=0)
        status = access.get_status("q")
        fake_script_text = "scripttext"
        reduction_run_v0 = create_reduction_run_record(experiment, instrument, FakeMessage(), 0, fake_script_text,
                                                       status)
        reduction_run_v0.save()
        reduction_run_v1 = create_reduction_run_record(experiment, instrument, FakeMessage(), 1, fake_script_text,
                                                       status)
        reduction_run_v1.save()
        reduction_run_v2 = create_reduction_run_record(experiment, instrument, FakeMessage(), 2, fake_script_text,
                                                       status)
        reduction_run_v2.save()

        assert access.find_highest_run_version(experiment, 1234567) == 3

        reduction_run_v0.delete()
        reduction_run_v1.delete()
        reduction_run_v2.delete()
        experiment.delete()
        instrument.delete()

    # pylint:disable=no-self-use
    def test_save_record(self):
        """
        Test: .save() is called on the provided object
        When: Calling save_record()
        """
        mock_record = Mock()
        access.save_record(mock_record)
        mock_record.save.assert_called_once()

    def test_get_status_with_invalid_status_value(self):
        """
        Test: When access.get_status is called with an invalid status_value a ValueError is raised
        When: Calling access.get_status()
        """
        self.assertRaises(ValueError, access.get_status, "test")
