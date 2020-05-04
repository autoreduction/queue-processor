# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the manual job submission script
"""
import re
import unittest
import json
from mock import Mock, patch, MagicMock
import scripts.manual_operations.manual_submission as ms
from scripts.manual_operations import manual_submission
from utils.clients.database_client import DatabaseClient
from utils.clients.icat_client import ICATClient
from utils.clients.queue_client import QueueClient


# pylint:disable=no-self-use
class TestManualSubmission(unittest.TestCase):  # TODO: Update the tests
    """
    Test manual_submission.py
    """
    def setUp(self):
        """ Creates test variables used throughout the test suite """
        self.location_and_rb_args = [DatabaseClient(), ICATClient(),
                                     "instrument", -1, "file_ext"]
        self.submit_run_args = [QueueClient(), -1, "instrument",
                                "data_file_location", -1]
        self.valid_return = ("location", "rb")

    def make_mock_return_object(self, return_from):
        """ Creates a MagicMock object in a format which mimics the format of
        an object returned from ICAT or the auto-reduction database
        :param return_from: A string representing what type of return object
        to be mocked
        :return: The formatted MagicMock object """
        ret_obj = [MagicMock()]
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

    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_database', return_value=None)
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_checks_database_then_icat(self, mock_from_icat, mock_from_database):
        """
        Test: Data for a given run is searched for in the database before calling ICAT
        When: get_location_and_rb is called for a datafile which isn't in the database
        """
        ms.get_location_and_rb(*self.location_and_rb_args)
        mock_from_database.assert_called_once()
        mock_from_icat.assert_called_once()

    @patch('sqlalchemy.engine.result.ResultProxy.fetchall')
    def test_get_from_database(self, mock_fetchall):
        """
        Test: Data for a given run can be retrieved from the database in the expected format
        When: get_location_and_rb_from_database is called and the data is present
        in the database
        """
        mock_fetchall.side_effect = ["_test_connection_return",
                                     self.make_mock_return_object("db_location"),
                                     self.make_mock_return_object("db_rb")]
        location_and_rb = ms.get_location_and_rb_from_database(self.location_and_rb_args[0], self.location_and_rb_args[3])
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_get_from_icat_when_file_exists_without_zeroes(self, mock_query):
        """
        Test: Data for a given run can be retrieved from ICAT in the expected format
        When: get_location_and_rb_from_icat is called and the data is present in ICAT
        """
        mock_query.return_value = self.make_mock_return_object("icat")
        location_and_rb = ms.get_location_and_rb_from_icat(*self.location_and_rb_args[1:])
        mock_query.assert_called_once()
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_get_from_icat_when_file_exists_with_zeroes(self, mock_query):
        """
        Test: Data for a given run can be retrieved from ICAT in the expected format
        When: get_location_and_rb_from_icat is called and the data is present in ICAT
        but named with prepended zeroes
        """
        # The below sets a sequence of return values (1st call -> ret=None ; 2nd call -> ret=Mock)
        mock_query.side_effect = [None, self.make_mock_return_object("icat")]
        location_and_rb = ms.get_location_and_rb_from_icat(*self.location_and_rb_args[1:])
        self.assertEqual(mock_query.call_count, 2)
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('utils.clients.icat_client.ICATClient.execute_query', return_value=None)
    @patch('sqlalchemy.engine.result.ResultProxy.fetchall', return_value=[])
    def test_get_when_does_not_exist(self, mock_db_fetchall, mock_icat_query):
        """
        Test: A SystemExit is raised
        When: get_location_and_rb is called but the data requested doesn't exist
        """
        with self.assertRaises(SystemExit):
            ms.get_location_and_rb(*self.location_and_rb_args)
        # Below: '>=2' factors in DatabaseClient._test_connection but doesn't require it
        self.assertTrue(mock_db_fetchall.call_count >= 2)
        self.assertTrue(mock_icat_query.call_count == 2)

    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_database')
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_when_run_number_not_int(self, mock_from_icat, mock_from_database):
        """
        Test: A SystemExit is raised and neither the database nor ICAT are checked for data
        When: get_location_and_rb is called with a run_number which cannot be cast as an int
        """
        args = self.location_and_rb_args
        args[3] = "string_rb_number"
        with self.assertRaises(SystemExit):
            ms.get_location_and_rb(*args)
        mock_from_icat.assert_not_called()
        mock_from_database.assert_not_called()

    @patch('utils.clients.queue_client.QueueClient.send', return_value=None)
    def test_submit_run(self, mock_send):
        """
        Test: A given run is submitted to the DataReady queue
        When: submit_run is called with valid arguments
        """
        ms.submit_run(*self.submit_run_args)
        json_obj = self.get_json_object(*self.submit_run_args[1:], -1)
        mock_send.assert_called_with('/queue/DataReady', json_obj, priority=1)
