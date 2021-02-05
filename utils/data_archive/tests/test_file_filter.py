# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for the file filtering functions
"""
import datetime
import os
import shutil
import time
import tempfile
import unittest
from collections import Counter

from utils.data_archive.file_filter import (check_file_extension, filter_files_by_extension, filter_files_by_time)


# pylint:disable=missing-docstring, invalid-name
class TestFileFilters(unittest.TestCase):
    def test_file_ext_valid_file_in_list(self):
        self.assertTrue(check_file_extension('test.nxs', '.nxs'))

    def test_file_ext_valid_uppercase_file(self):
        self.assertTrue(check_file_extension('TEST.NXS', '.nxs'))

    def test_file_ext_valid_uppercase_extension(self):
        self.assertTrue(check_file_extension('test.nxs', '.NXS'))

    def test_file_ext_valid_multi_ext(self):
        self.assertTrue(check_file_extension('test.txt', ('.nxs', '.txt')))

    def test_file_ext_invalid(self):
        self.assertFalse(check_file_extension('test.nxs', '.txt'))

    def test_file_ext_empty_input(self):
        self.assertFalse(check_file_extension('', '.nxs'))

    def test_file_ext_empty_extension(self):
        self.assertFalse(check_file_extension('test.nxs', ''))

    def test_valid_filter_file_by_ext_single(self):
        files = ['test.txt', 'test.nxs', 'test1.txt', 'test.log']
        expected = ['test.txt', 'test1.txt']
        actual = filter_files_by_extension(files, '.txt')
        self.assertEqual(actual, expected)

    def test_valid_filter_file_by_ext_multi(self):
        files = ['test.txt', 'test.nxs', 'test1.txt', 'test.log']
        expected = ['test.txt', 'test1.txt', 'test.log']
        actual = filter_files_by_extension(files, ('.txt', '.log'))
        self.assertEqual(actual, expected)

    def test_invalid_filter_file_by_ext_empty_ext(self):
        files = ['test.txt', 'test.nxs', 'test1.txt', 'test.log']
        expected = []
        actual = filter_files_by_extension(files, '')
        self.assertEqual(actual, expected)

    def test_invalid_filter_file_by_ext_empty_input(self):
        files = []
        expected = []
        actual = filter_files_by_extension(files, ('.txt', '.log'))
        self.assertEqual(actual, expected)


class TestTimeFilterFiles(unittest.TestCase):
    """
    Test the functionality that filters files by modification time
    """
    def setUp(self):
        """
        Create test directory and populate it with some test files
        """
        self.test_output_directory = tempfile.mkdtemp()
        list_of_test_files = ['test.nxs', 'test.txt', 'test.jpg', 'test.raw']
        for file_name in list_of_test_files:
            file_path = os.path.join(self.test_output_directory, file_name)
            with open(file_path, 'w+') as new_file:
                new_file.write("test_file")
        for file_name in list_of_test_files:
            file_path = os.path.join(self.test_output_directory, file_name)
            os.utime(file_path, (100.0, 100.0))

    def test_filter_files_by_time_no_new(self):
        """
        Test that when no new files are added, nothing is returned
        """
        cut_off = datetime.datetime.fromtimestamp(1000.0)
        actual = filter_files_by_time(self.test_output_directory, cut_off)
        self.assertEqual(actual, [])

    def test_filter_files_by_time_add_single(self):
        """
        Test that when one new file is added later than the time filter it is returned
        """
        cut_off = datetime.datetime.fromtimestamp(1000.0)
        new_file_path = os.path.join(self.test_output_directory, 'new_file.txt')
        time.sleep(0.2)
        with open(new_file_path, 'w+') as new_file:
            new_file.write("test_file")
        actual = filter_files_by_time(self.test_output_directory, cut_off)
        self.assertEqual(actual, [new_file_path])

    def test_filter_files_by_time_add_multi(self):
        """
        Test that when multiple files are added later than
        the time filter they are returned
        """
        cut_off = datetime.datetime.fromtimestamp(1000.0)
        new_file_paths = [
            os.path.join(self.test_output_directory, 'new_file.txt'),
            os.path.join(self.test_output_directory, 'new_file1.txt')
        ]
        for file_path in new_file_paths:
            with open(file_path, 'w+') as new_file:
                new_file.write("test_file")
        actual = filter_files_by_time(self.test_output_directory, cut_off)
        # We use a counter as we cannot guarantee the order of the return from os.listdir
        self.assertEqual(Counter(actual), Counter(new_file_paths))

    def test_filter_files_by_time_with_timestamp(self):
        """
        Check that filter files by time accepts datetime object and timestamps
        """
        dt_cut_off = datetime.datetime(1970, 1, 1)
        timestamp = 1000
        self.assertIsNotNone(filter_files_by_time(self.test_output_directory, dt_cut_off))
        self.assertIsNotNone(filter_files_by_time(self.test_output_directory, timestamp))

    def test_filter_files_by_time_invalid_time_input(self):
        """
        Test that string is not a valid time input
        """
        error_msg = "cut_off_time must be a numerical timestamp or datetime object. Type found: {}"
        self.assertRaisesRegex(RuntimeError, error_msg.format("<class 'str'>"), filter_files_by_time,
                               self.test_output_directory, "string")

    def tearDown(self):
        """
        Delete the testing directory
        """
        shutil.rmtree(self.test_output_directory)
