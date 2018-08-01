"""
tests for the file filtering functions
"""
import datetime
import os
import shutil
import time
import unittest

from utils.archive_explorer.file_filter import (check_file_extension,
                                                filter_files_by_extension,
                                                filter_files_by_time)


class TestFileFilters(unittest.TestCase):

    def test_check_file_ext_valid_file_in_list(self):
        self.assertTrue(check_file_extension('test.nxs', '.nxs'))

    def test_check_file_ext_valid_uppercase_file(self):
        self.assertTrue(check_file_extension('TEST.NXS', '.nxs'))

    def test_check_file_ext_valid_uppercase_extension(self):
        self.assertTrue(check_file_extension('test.nxs', '.NXS'))

    def test_check_file_ext_valid_multi_ext(self):
        self.assertTrue(check_file_extension('test.txt', ('.nxs', '.txt')))

    def test_check_file_ext_invalid(self):
        self.assertFalse(check_file_extension('test.nxs', '.txt'))

    def test_check_file_ext_empty_input(self):
        self.assertFalse(check_file_extension('', '.nxs'))

    def test_check_file_ext_empty_extension(self):
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

    def setUp(self):
        self.test_output_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  'test-output')
        os.makedirs(self.test_output_directory)
        list_of_test_files = ['test.nxs', 'test.txt', 'test.jpg', 'test.raw']
        for file_name in list_of_test_files:
            with open(os.path.join(self.test_output_directory, file_name), 'w+') as new_file:
                new_file.write("test_file")
        time.sleep(0.2)
        self.creation_time = datetime.datetime.now()

    def test_filter_files_by_time_no_new(self):
        actual = filter_files_by_time(self.test_output_directory, self.creation_time)
        self.assertEqual(actual, [])

    def test_filter_files_by_time_add_single(self):
        new_file_path = os.path.join(self.test_output_directory, 'new_file.txt')
        with open(new_file_path, 'w+') as new_file:
            new_file.write("test_file")
        actual = filter_files_by_time(self.test_output_directory, self.creation_time)
        self.assertEqual(actual, [new_file_path])

    def test_filter_files_by_time_add_multi(self):
        new_file_paths = [os.path.join(self.test_output_directory, 'new_file.txt'),
                          os.path.join(self.test_output_directory, 'new_file1.txt')]
        for file_path in new_file_paths:
            with open(file_path, 'w+') as new_file:
                new_file.write("test_file")
        actual = filter_files_by_time(self.test_output_directory, self.creation_time)
        self.assertEqual(actual, new_file_paths)

    def tearDown(self):
        shutil.rmtree(self.test_output_directory)
