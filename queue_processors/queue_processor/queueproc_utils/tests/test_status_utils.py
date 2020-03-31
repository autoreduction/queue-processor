# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module to test the utility functions for status records in the database
"""
import unittest

from mock import patch

from queue_processors.queue_processor.queueproc_utils.status_utils import StatusUtils
from queue_processors.queue_processor.queueproc_utils.tests.\
    compare_db_object import compare_db_objects
from queue_processors.queue_processor.orm_mapping import Status


# pylint:disable=missing-class-docstring,missing-function-docstring
class TestStatusUtils(unittest.TestCase):

    def setUp(self):
        self.status_utils = StatusUtils()
        self.completed_status = Status(value='Completed')

    @patch('queue_processors.queue_processor.queueproc_utils.status_utils.StatusUtils._get_status')
    def test_get_error(self, mock_get_status):
        self.status_utils.get_error()
        mock_get_status.assert_called_with("Error")

    @patch('queue_processors.queue_processor.queueproc_utils.status_utils.StatusUtils._get_status')
    def test_get_completed(self, mock_get_status):
        self.status_utils.get_completed()
        mock_get_status.assert_called_with("Completed")

    @patch('queue_processors.queue_processor.queueproc_utils.status_utils.StatusUtils._get_status')
    def test_get_processing(self, mock_get_status):
        self.status_utils.get_processing()
        mock_get_status.assert_called_with("Processing")

    @patch('queue_processors.queue_processor.queueproc_utils.status_utils.StatusUtils._get_status')
    def test_get_queued(self, mock_get_status):
        self.status_utils.get_queued()
        mock_get_status.assert_called_with("Queued")

    @patch('queue_processors.queue_processor.queueproc_utils.status_utils.StatusUtils._get_status')
    def test_get_skipped(self, mock_get_status):
        self.status_utils.get_skipped()
        mock_get_status.assert_called_with("Skipped")

    @patch('queue_processors.queue_processor.base.session.query')
    def test_get_status_valid(self, mock_query):
        """
        Test that the expected Status object is returned if it exists
        Note: we are mocking the database return to ensure it does exist
        """
        mock_query.return_value.filter_by.return_value = [self.completed_status]
        # pylint:disable=protected-access
        actual = self.status_utils._get_status('valid')
        self.assertTrue(compare_db_objects(actual, self.completed_status))

    @patch('queue_processors.queue_processor.queueproc_utils.status_utils.'
           'StatusUtils._create_new_status')
    @patch('queue_processors.queue_processor.base.session.query')
    def test_get_status_create_new(self, mock_query, mock_create_new_status):
        """
        Ensure that if we attempt to a access a Status record that does not exist in the database,
        we attempt to create it by calling the create method
        Note: We do not test the create method in this test (here it is mocked)
        """
        mock_query.return_value.filter_by.return_value = [None]
        # pylint:disable=protected-access
        self.status_utils._get_status('new')
        mock_create_new_status.assert_called_once_with('new')

    @patch('queue_processors.queue_processor.base.session.add')
    @patch('queue_processors.queue_processor.base.session.commit')
    @patch('queue_processors.queue_processor.base.session.query')
    def test_create_new_status(self, mock_query, mock_commit, mock_add):
        """
        Ensure that a new status record can be created and added to the database as expected
        Note: Actual DB interactions are mocked
        """
        expected = Status(value='new')
        mock_query.return_value.filter_by.return_value = [expected]
        # pylint:disable=protected-access
        actual = self.status_utils._create_new_status('new')
        args, _ = mock_add.call_args
        self.assertTrue(compare_db_objects(args[0], expected))
        mock_commit.assert_called_once()
        compare_db_objects(actual, expected)
