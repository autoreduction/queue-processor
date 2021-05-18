# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the manual job submission script
"""
from unittest.mock import MagicMock, Mock, patch

from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.clients.icat_client import ICATClient
from autoreduce_utils.clients.queue_client import QueueClient
from autoreduce_utils.message.message import Message
from django.test import TestCase
from autoreduce_qp.scripts.manual_operations import manual_submission as ms
from autoreduce_qp.scripts.manual_operations.tests.test_manual_remove import (create_experiment_and_instrument,
                                                                              make_test_run)


# pylint:disable=no-self-use
class TestManualSubmission(TestCase):
    """
    Test manual_submission.py
    """
    fixtures = ["status_fixture"]

    def setUp(self):
        """ Creates test variables used throughout the test suite """
        self.loc_and_rb_args = {
            "icat_client": MagicMock(name="ICATClient"),
            "instrument": "instrument",
            "run_number": -1,
            "file_ext": "file_ext"
        }
        self.sub_run_args = {
            "active_mq_client": MagicMock(name="QueueClient"),
            "rb_number": -1,
            "instrument": "instrument",
            "data_file_location": "data_file_location",
            "run_number": -1
        }
        self.valid_return = ("location", "rb")

        self.experiment, self.instrument = create_experiment_and_instrument()

        self.run1 = make_test_run(self.experiment, self.instrument, "1")
        self.run1.data_location.create(file_path='test/file/path/2.raw')

    def mock_database_query_result(self, side_effects):
        """ Sets the return value(s) of database queries to those provided
        :param side_effects: A list of values to return from the database query (in sequence)"""
        mock_query_result = MagicMock(name="mock_query_result")
        mock_query_result.fetchall.side_effect = side_effects

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

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_location_and_rb_from_database',
           return_value=None)
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_checks_database_then_icat(self, mock_from_icat, mock_from_database):
        """
        Test: Data for a given run is searched for in the database before calling ICAT
        When: get_location_and_rb is called for a datafile which isn't in the database
        """
        ms.get_location_and_rb(**self.loc_and_rb_args)
        mock_from_database.assert_called_once()
        mock_from_icat.assert_called_once()

    @patch('model.database.access.get_reduction_run')
    def test_get_from_database_no_run(self, mock_get_run):
        """
        Test: None is returned
        When: get_location_and_rb_from_database can't find a ReductionRun record
        """
        mock_get_run.return_value = None
        self.assertIsNone(ms.get_location_and_rb_from_database('GEM', 123))
        mock_get_run.assert_not_called()

    def test_get_from_database(self):
        """
        Test: Data for a given run can be retrieved from the database in the expected format
        When: get_location_and_rb_from_database is called and the data is present
        in the database
        """
        actual = ms.get_location_and_rb_from_database('ARMI', 101)
        # Values from testing database
        expected = ('test/file/path/2.raw', 1231231)
        self.assertEqual(expected, actual)

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_icat_instrument_prefix')
    def test_get_from_icat_when_file_exists_without_zeroes(self, _):
        """
        Test: Data for a given run can be retrieved from ICAT in the expected format
        When: get_location_and_rb_from_icat is called and the data is present in ICAT
        """
        self.loc_and_rb_args["icat_client"].execute_query.return_value = self.make_query_return_object("icat")
        location_and_rb = ms.get_location_and_rb_from_icat(**self.loc_and_rb_args)
        self.loc_and_rb_args["icat_client"].execute_query.assert_called_once()
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_icat_instrument_prefix', return_value='MAR')
    def test_icat_uses_prefix_mapper(self, _):
        """
        Test: The instrument shorthand name is used
        When: querying ICAT with function get_location_and_rb_from_icat
        """
        icat_client = Mock()
        data_file = Mock()
        data_file.location = 'location'
        data_file.dataset.investigation.name = 'inv_name'
        # Add return here to ensure we do NOT try fall through cases
        # and do NOT have to deal with multiple calls to mock
        icat_client.execute_query.return_value = [data_file]
        actual_loc, actual_inv_name = ms.get_location_and_rb_from_icat(icat_client, 'MARI', '123', 'nxs')
        self.assertEqual('location', actual_loc)
        self.assertEqual('inv_name', actual_inv_name)
        icat_client.execute_query.assert_called_once_with("SELECT df FROM Datafile df WHERE"
                                                          " df.name = 'MAR00123.nxs' INCLUDE"
                                                          " df.dataset AS ds, ds.investigation")

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_icat_instrument_prefix')
    def test_get_location_and_rb_from_icat_when_first_file_not_found(self, _):
        """
        Test: that get_location_and_rb_from_icat can handle a number of failed ICAT
        data file search attempts before it returns valid data file and check that
        expected format is then still returned.
        When: get_location_and_rb_from_icat is called and the file is initially not
        found in ICAT.
        """
        # icat returns: not found a number of times before file found
        self.loc_and_rb_args["icat_client"].execute_query.side_effect =\
            [None, None, None, self.make_query_return_object("icat")]
        # call the method to test
        location_and_rb = ms.get_location_and_rb_from_icat(**self.loc_and_rb_args)
        # how many times have icat been called
        self.assertEqual(self.loc_and_rb_args["icat_client"].execute_query.call_count, 4)
        # check returned format is OK
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_location_and_rb_from_database')
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_when_run_number_not_int(self, mock_from_icat, mock_from_database):
        """
        Test: A SystemExit is raised and neither the database nor ICAT are checked for data
        When: get_location_and_rb is called with a run_number which cannot be cast to int
        """
        self.loc_and_rb_args["run_number"] = "invalid run number"
        with self.assertRaises(SystemExit):
            ms.get_location_and_rb(**self.loc_and_rb_args)
        mock_from_icat.assert_not_called()
        mock_from_database.assert_not_called()

    def test_submit_run(self):
        """
        Test: A given run is submitted to the DataReady queue
        When: submit_run is called with valid arguments
        """
        ms.submit_run(**self.sub_run_args)
        message = Message(rb_number=self.sub_run_args["rb_number"],
                          instrument=self.sub_run_args["instrument"],
                          data=self.sub_run_args["data_file_location"],
                          run_number=self.sub_run_args["run_number"],
                          facility="ISIS",
                          started_by=-1)
        self.sub_run_args["active_mq_client"].send.assert_called_with('/queue/DataReady', message, priority=1)

    @patch('icat.Client')
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.ICATClient.connect')
    def test_icat_login_valid(self, mock_connect, _):
        """
        Test: A valid ICAT client is returned
        When: We can log in via the client
        Note: We mock the connect so it does not actual perform the connect (default pass)
        """
        actual = ms.login_icat()
        self.assertIsInstance(actual, ICATClient)
        mock_connect.assert_called_once()

    @patch('icat.Client')
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.ICATClient.connect')
    def test_icat_login_invalid(self, mock_connect, _):
        """
        Test: None is returned
        When: We are unable to log in via the icat client
        """
        con_exp = ConnectionException('icat')
        mock_connect.side_effect = con_exp
        self.assertIsNone(ms.login_icat())

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.QueueClient.connect')
    def test_queue_login_valid(self, _):
        """
        Test: A valid Queue client is returned
        When: We can log in via the queue client
        Note: We mock the connect so it does not actual perform the connect (default pass)
        """
        actual = ms.login_queue()
        self.assertIsInstance(actual, QueueClient)

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.QueueClient.connect')
    def test_queue_login_invalid(self, mock_connect):
        """
        Test: An exception is raised
        When: We are unable to log in via the client
        """
        con_exp = ConnectionException('Queue')
        mock_connect.side_effect = con_exp
        self.assertRaises(RuntimeError, ms.login_queue)

    def test_submit_run_no_amq(self):
        """
        Test: That there is an early return
        When: Calling submit_run with active_mq as None
        """
        self.assertIsNone(
            ms.submit_run(active_mq_client=None,
                          rb_number=None,
                          instrument=None,
                          data_file_location=None,
                          run_number=None))

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.login_icat')
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.login_queue')
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_location_and_rb')
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.submit_run')
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_run_range')
    def test_main_valid(self, mock_run_range, mock_submit, mock_get_loc, mock_queue, mock_icat):
        """
        Test: The control methods are called in the correct order
        When: main is called and the environment (client settings, input, etc.) is valid
        """
        mock_run_range.return_value = range(1111, 1112)

        # Setup Mock clients
        mock_icat_client = Mock()
        mock_queue_client = Mock()

        # Assign Mock return values
        mock_queue.return_value = mock_queue_client
        mock_icat.return_value = mock_icat_client
        mock_get_loc.return_value = ('test/file/path', 2222)

        # Call functionality
        ms.main(instrument='TEST', first_run=1111)

        # Assert
        mock_run_range.assert_called_with(1111, last_run=None)
        mock_icat.assert_called_once()
        mock_queue.assert_called_once()
        mock_get_loc.assert_called_once_with(mock_icat_client, 'TEST', 1111, "nxs")
        mock_submit.assert_called_once_with(mock_queue_client, 2222, 'TEST', 'test/file/path', 1111)

    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.login_icat')
    @patch('autoreduce_qp.scripts.manual_operations.manual_submission.get_run_range')
    def test_main_bad_client(self, mock_get_run_range, mock_icat):
        """
        Test: A RuntimeError is raised
        When: Neither ICAT or Database connections can be established
        """
        mock_get_run_range.return_value = range(1111, 1112)
        mock_icat.return_value = None
        self.assertRaises(RuntimeError, ms.main, 'TEST', 1111)
        mock_get_run_range.assert_called_with(1111, last_run=None)
        mock_icat.assert_called_once()
