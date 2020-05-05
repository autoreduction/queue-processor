# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the manual job submission script
"""
import unittest
import json
from mock import patch, MagicMock
import scripts.manual_operations.manual_submission as ms


# pylint:disable=no-self-use
class TestManualSubmission(unittest.TestCase):
    """
    Test manual_submission.py
    """
    def setUp(self):
        """ Creates test variables used throughout the test suite """
        self.loc_and_rb_args = [MagicMock(name="DatabaseClient"), MagicMock(name="ICATClient"),
                                "instrument", -1, "file_ext"]
        self.sub_run_args = [MagicMock(name="QueueClient"),
                             -1, "instrument", "data_file_location", -1]
        self.valid_return = ("location", "rb")

    def mock_database_query_result(self, side_effects):
        """ Sets the return value(s) of database queries to those provided
        :param side_effects: A list of values to return from the database query (in sequence)"""
        # Note: SQLAlchemy query call complicated to mock (the code below).
        #  This code will need to change when Django ORM implemented anyway.
        mock_query_result = MagicMock(name="mock_query_result")
        mock_query_result.fetchall.side_effect = side_effects
        mock_connection = MagicMock(name="mock_connection")
        mock_connection.execute.return_value = mock_query_result
        self.loc_and_rb_args[0].connect.return_value = mock_connection

    def make_query_return_object(self, return_from):
        """ Creates a MagicMock object in a format which mimics the format of
        an object returned from a query to ICAT or the auto-reduction database
        :param return_from: A string representing what type of return object
        to be mocked
        :return: The formatted MagicMock object """
        ret_obj = [MagicMock(name="Return object")]
        if return_from == "icat":
            ret_obj[0].location = self.valid_return[0]
            ret_obj[0].dataset.investigation.name = self.valid_return[1]
        elif return_from == "db_location":
            ret_obj[0].file_path = self.valid_return[0]
        elif return_from == "db_rb":
            ret_obj[0].reference_number = self.valid_return[1]
        return ret_obj

    @staticmethod
    def get_json_object(rb_number, instrument, data_file_location, run_number, started_by):
        """ :return: The JSON object which should be sent to DataReady """
        data_dict = {"rb_number": rb_number,
                     "instrument": instrument,
                     "data": data_file_location,
                     "run_number": run_number,
                     "facility": "ISIS",
                     "started_by": started_by}
        return json.dumps(data_dict)

    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_database',
           return_value=None)
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_checks_database_then_icat(self, mock_from_icat, mock_from_database):
        """
        Test: Data for a given run is searched for in the database before calling ICAT
        When: get_location_and_rb is called for a datafile which isn't in the database
        """
        ms.get_location_and_rb(*self.loc_and_rb_args)
        mock_from_database.assert_called_once()
        mock_from_icat.assert_called_once()

    def test_get_from_database(self):
        """
        Test: Data for a given run can be retrieved from the database in the expected format
        When: get_location_and_rb_from_database is called and the data is present
        in the database
        """
        side_effects = [self.make_query_return_object("db_location"),
                        self.make_query_return_object("db_rb")]
        self.mock_database_query_result(side_effects)

        location_and_rb = ms.get_location_and_rb_from_database(self.loc_and_rb_args[0],
                                                               self.loc_and_rb_args[3])
        self.assertEqual(location_and_rb, self.valid_return)

    def test_get_from_icat_when_file_exists_without_zeroes(self):
        """
        Test: Data for a given run can be retrieved from ICAT in the expected format
        When: get_location_and_rb_from_icat is called and the data is present in ICAT
        """
        self.loc_and_rb_args[1].execute_query.return_value = self.make_query_return_object("icat")
        location_and_rb = ms.get_location_and_rb_from_icat(*self.loc_and_rb_args[1:])
        self.loc_and_rb_args[1].execute_query.assert_called_once()
        self.assertEqual(location_and_rb, self.valid_return)

    def test_get_from_icat_when_file_exists_with_zeroes(self):
        """
        Test: Data for a given run can be retrieved from ICAT in the expected format
        When: get_location_and_rb_from_icat is called and the data is present in ICAT
        but named with prepended zeroes
        """
        self.loc_and_rb_args[1].execute_query.side_effect =\
            [None, self.make_query_return_object("icat")]
        location_and_rb = ms.get_location_and_rb_from_icat(*self.loc_and_rb_args[1:])
        self.assertEqual(self.loc_and_rb_args[1].execute_query.call_count, 2)
        self.assertEqual(location_and_rb, self.valid_return)

    def test_get_when_does_not_exist(self):
        """
        Test: A SystemExit is raised
        When: get_location_and_rb is called but the data requested doesn't exist
        """
        mock_db_connection = MagicMock(name="mock_connection")
        self.loc_and_rb_args[0].connect.return_value = mock_db_connection
        self.loc_and_rb_args[1].execute_query.return_value = None

        with self.assertRaises(SystemExit):
            ms.get_location_and_rb(*self.loc_and_rb_args)
        self.assertTrue(mock_db_connection.execute.call_count == 1)
        self.assertTrue(self.loc_and_rb_args[1].execute_query.call_count == 2)

    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_database')
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_when_run_number_not_int(self, mock_from_icat, mock_from_database):
        """
        Test: A SystemExit is raised and neither the database nor ICAT are checked for data
        When: get_location_and_rb is called with a run_number which cannot be cast as an int
        """
        self.loc_and_rb_args[3] = "string_rb_number"
        with self.assertRaises(SystemExit):
            ms.get_location_and_rb(*self.loc_and_rb_args)
        mock_from_icat.assert_not_called()
        mock_from_database.assert_not_called()

    @patch('json.dumps', return_value="json_dump")
    def test_submit_run(self, mock_json_dump):
        """
        Test: A given run is submitted to the DataReady queue
        When: submit_run is called with valid arguments
        """
        ms.submit_run(*self.sub_run_args)
        self.sub_run_args[0].send.assert_called_with('/queue/DataReady',
                                                     mock_json_dump.return_value,
                                                     priority=1)
