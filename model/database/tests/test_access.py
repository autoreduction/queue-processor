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

from mock import patch, Mock

from model.database import access


class TestAccess(unittest.TestCase):

    @patch('utils.clients.django_database_client.DatabaseClient.connect')
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

    @patch('model.database.access.save_record')
    def test_get_instrument_does_not_exist(self, mock_save):
        """
        Test: A new instrument record is created
        When: create is true and no matching instrument can be found in the database

        Note: As we do not actually save the object, we cannot assert values of it
        These are only stored when it enters the database
        """
        db = access.start_database()
        actual = access.get_instrument('Not an instrument', create=True)
        self.assertIsNotNone(actual)
        self.assertIsInstance(actual, db.data_model.Instrument)
        mock_save.assert_called_once()

    def test_get_instrument_invalid(self):
        """
        Test: None is returned
        When: get_instrument is called with an instrument that does not exist
        """
        actual = access.get_instrument('Fake instrument')
        self.assertIsNone(actual)

    def test_save_record(self):
        """
        Test: .save() is called on the provided object
        When: Calling save_record()
        """
        mock_record = Mock()
        access.save_record(mock_record)
        mock_record.save.assert_called_once()

    # pylint:disable=no-self-use
    @patch('model.database.access.start_database')
    def test_get_reduction_run_valid(self, mock_start_db):
        """
        Test: A ReductionRun record is returned
        When: get_reduction_run is called with values that match a database record
        """
        mock_db = Mock()
        mock_start_db.return_value = mock_db
        access.get_reduction_run('GEM', 1)
        mock_db.data_model.ReductionRun.objects.filter.assert_called_once()

    def test_get_reduction_run_invalid(self):
        """
        Test: None is returned
        When: get_reduction_run is called values not in the database
        """
        actual = access.get_reduction_run('GEM', 0)
        self.assertIsNone(actual.first())
