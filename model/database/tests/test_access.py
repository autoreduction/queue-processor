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

from mock import patch, Mock, NonCallableMock

from model.database import access


class TestAccess(unittest.TestCase):
    """
    Test the access functionality for the database
    """

    # pylint:disable=no-self-use
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
        database = access.start_database()
        actual = access.get_instrument('Not an instrument', create=True)
        self.assertIsNotNone(actual)
        self.assertIsInstance(actual, database.data_model.Instrument)
        mock_save.assert_called_once()

    def test_get_instrument_invalid(self):
        """
        Test: None is returned
        When: get_instrument is called with an instrument that does not exist
        """
        actual = access.get_instrument('Fake instrument')
        self.assertIsNone(actual)

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
        self.assertEqual(123, actual.reference_number)

    @patch('model.database.access.save_record')
    def test_get_experiment_create(self, mock_save):
        """
        Test: An Experiment record is created
        When: get_experiment is called with create option True
        """
        database = access.start_database()
        actual = access.get_experiment(rb_number=9999999)
        self.assertIsInstance(actual, database.data_model.Experiment)
        mock_save.assert_called_once()

    def test_get_software(self):
        """
        Test: The correct Software record is returned
        When: get_software is called with values that match a database record
        """
        actual = access.get_software('Mantid', '4.0')
        self.assertIsNotNone(actual)
        self.assertEqual('Mantid', actual.name)
        self.assertEqual('4.0', actual.version)

    @patch('model.database.access.save_record')
    def test_get_software_create(self, mock_save):
        """
        Test: A Software record is created
        When: get_software is called with create option True
        """
        database = access.start_database()
        actual = access.get_software(name='Fake', version='test', create=True)
        self.assertIsNotNone(actual)
        self.assertIsInstance(actual, database.data_model.Software)
        mock_save.assert_called_once()

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

    @patch('model.database.access.start_database')
    def test_find_highest_run_version(self, db_layer):
        """
        Test: The expected highest version number is returned
        When: Calling find_highest_run_version
        """
        run_objects = db_layer.return_value.data_model.ReductionRun.objects
        db_call = run_objects.filter.return_value\
            .filter.return_value\
            .order_by.return_value\
            .first

        for test_in, output in [(None, -1), (0, 0), (1, 1), (5, 5)]:
            if test_in is None:
                db_call.return_value = None
            else:
                db_call.return_value = NonCallableMock()
                db_call.return_value.run_version = test_in

            actual = access.find_highest_run_version('rb_num', 'run_no')
            run_objects.filter.assert_called_with(run_number='run_no')
            run_objects.filter.return_value.filter\
                .assert_called_with(experiment='rb_num')

            self.assertEqual(output, actual)

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
