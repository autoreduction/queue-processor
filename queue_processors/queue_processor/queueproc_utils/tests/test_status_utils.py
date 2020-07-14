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

from utils.clients.django_database_client import DjangoORM


# pylint:disable=missing-class-docstring,missing-function-docstring
class TestStatusUtils(unittest.TestCase):

    def setUp(self):
        self.status_utils = StatusUtils()
        database = DjangoORM()
        database.connect()
        self.completed_status = database.data_model.Status(value='Completed')
        self.status_type = database.data_model.Status

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

    def test_get_status_valid(self):
        """
        Test that the expected Status object is returned if it exists
        Note: we are mocking the database return to ensure it does exist
        """
        # pylint:disable=protected-access
        actual = self.status_utils._get_status('valid')
        self.assertIsNotNone(actual)
        self.assertIsInstance(actual, self.status_type)
