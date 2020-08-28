# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for log_handler
"""
# Internal Dependencies
from utils.logger.log_handler import GetLogger

# External Dependencies
import unittest
from mock import patch
import logging


class TestGetLogger(unittest.TestCase):

    @patch("utils.logger.log_handler.GetLogger.create_logger", return_value=None)
    def test_set_log_level(self, mock_create_logger):
        """
        Test: set_log_level returns a value equal to logging.DEBUG
        When: called with a log level argument of DEBUG
        """
        actual = GetLogger().set_log_level(log_level="DEBUG")
        expected = logging.DEBUG
        self.assertEqual(actual, expected)

    @patch("utils.logger.log_handler.GetLogger.create_logger", return_value=None)
    def test_set_log_format(self, mock_create_logger):
        """
        Test: set_log_format() returns the correct log format
        When: called
        """
        actual = GetLogger().set_log_format()
        expected = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
        self.assertEqual(type(actual), type(expected))

    @patch("utils.logger.log_handler.GetLogger.create_logger", return_value=None)
    def test_set_stream_handler(self, _):
        """
        Test: set_stream_handler sets the correct logging.StreamHandler() format
        When: called
        """
        actual = GetLogger().set_stream_handler()
        expected = logging.StreamHandler('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
        self.assertEqual(type(actual), type(expected))

    @patch("utils.logger.log_handler.GetLogger.create_logger", return_value=None)
    def test_create_logger_with_stream(self, _):
        """
        Test: create_logger_with_stream returns object
        When: called with valid init values
        """
        with patch.object(GetLogger, "__init__", lambda w, x, y, z: None) as get_logger:
            c = GetLogger(None, None, None)
            c.log_level = 'DEBUG'
            c.log_file_name = None
            c.print_to_console = False
            self.assertIsInstance(c.create_logger(), object)
