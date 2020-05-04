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


# pylint:disable=too-few-public-methods
class DataFile:
    """
    Basic data file representation for testing
    """
    def __init__(self, df_name):
        self.name = df_name


def get_json_object(rb_number, instrument, data_file_location, run_number, started_by):
    """
    Return the JSON object that should be sent to DataReady
    """
    data_dict = {"rb_number": rb_number,
                 "instrument": instrument,
                 "data": data_file_location,
                 "run_number": run_number,
                 "facility": "ISIS",
                 "started_by": started_by}
    return json.dumps(data_dict)


# pylint:disable=no-self-use
class TestManualSubmission(unittest.TestCase):  # TODO: Update the tests
    """
    Test manual_submission.py
    """
    def setUp(self):
        # self.valid_value = "valid"
        self.location_and_rb_args = [DatabaseClient(), ICATClient(),
                                     "instrument", -1, "file_ext"]
        self.submit_run_args = [QueueClient(), -1, "instrument",
                                "data_file_location", -1]
        self.valid_return = ("location", "rb")

    def make_mock_return_object(self, return_from):
        ret_obj = [MagicMock()]
        if return_from == "icat":
            ret_obj[0].location = self.valid_return[0]
            ret_obj[0].dataset.investigation.name = self.valid_return[1]
        elif return_from == "db_location":
            ret_obj[0].file_path = self.valid_return[0]
        elif return_from == "db_rb":
            ret_obj[0].reference_number = self.valid_return[1]
        return ret_obj

    # TODO: test/whens

    # TODO: tests
    #   - test_get_calls_icat_then_database
    #   - test_get_from_database
    #   - test_get_from_icat_when_file_exists_without_zeroes
    #   - test_get_from_icat_when_file_exists_with_zeroes
    #   - test_get_when_file_does_not_exist

    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_database', return_value=None)
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_checks_database_then_icat(self, mock_from_icat, mock_from_database):
        """
        Test: A datafile is sought for in the database before icat
        When: get_location_and_rb is called and the datafile isn't in the database
        """
        mock_from_icat.return_value = self.valid_return
        result = ms.get_location_and_rb(*self.location_and_rb_args)
        self.assertEqual(self.valid_return, result)
        mock_from_database.assert_called_once()

    @patch('sqlalchemy.engine.result.ResultProxy.fetchall')
    def test_get_from_database(self, mock_fetchall):
        mock_fetchall.side_effect = ["_test_connection_return",
                                     self.make_mock_return_object("db_location"),
                                     self.make_mock_return_object("db_rb")]
        location_and_rb = ms.get_location_and_rb_from_database(self.location_and_rb_args[0], self.location_and_rb_args[3])
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_get_from_icat_when_file_exists_without_zeroes(self, mock_query):
        mock_query.return_value = self.make_mock_return_object("icat")
        location_and_rb = ms.get_location_and_rb_from_icat(*self.location_and_rb_args[1:])
        mock_query.assert_called_once()
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_get_from_icat_when_file_exists_with_zeroes(self, mock_query):
        # The below sets a sequence of return values (1st call -> ret=None ; 2nd call -> ret=Mock)
        mock_query.side_effect = [None, self.make_mock_return_object("icat")]
        location_and_rb = ms.get_location_and_rb_from_icat(*self.location_and_rb_args[1:])
        self.assertEqual(mock_query.call_count, 2)
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('utils.clients.icat_client.ICATClient.execute_query', return_value=None)
    @patch('sqlalchemy.engine.result.ResultProxy.fetchall', return_value=[])
    def test_get_when_file_does_not_exist(self, mock_db_fetchall, mock_icat_query):
        with self.assertRaises(SystemExit):
            ms.get_location_and_rb(*self.location_and_rb_args)
        # Below: '>=2' factors in DatabaseClient._test_connection but doesn't require it
        self.assertTrue(mock_db_fetchall.call_count >= 2)
        self.assertTrue(mock_icat_query.call_count == 2)

    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_database')
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_when_run_number_not_int(self, mock_from_icat, mock_from_database):
        args = self.location_and_rb_args
        args[3] = "string_rb_number"
        result = ms.get_location_and_rb(*args)
        self.assertIsNone(result)
        mock_from_icat.assert_not_called()
        mock_from_database.assert_not_called()

    @patch('utils.clients.queue_client.QueueClient.send', return_value=None)
    def test_submit_run(self, mock_send):
        """
        Check that a run is submitted successfully
        """
        ms.submit_run(*self.submit_run_args)
        json_obj = get_json_object(*self.submit_run_args[1:], -1)
        mock_send.assert_called_with('/queue/DataReady', json_obj, priority=1)
