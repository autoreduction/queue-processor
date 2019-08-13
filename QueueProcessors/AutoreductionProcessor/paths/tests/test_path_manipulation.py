import unittest

import QueueProcessors.AutoreductionProcessor.paths.path_manipulation as utils


class TestUtils(unittest.TestCase):

    def test_path_is_windows_true(self):
        self.assertTrue(utils.is_path_windows(r'C:\windows\path'))
        self.assertTrue(utils.is_path_windows('C:\\windows\\path'))
        self.assertTrue(utils.is_path_windows(r'C:\windows\path\file.nxs'))
        self.assertTrue(utils.is_path_windows('C:\\windows\\path\\file.nxs'))

    def test_path_is_windows_false(self):
        self.assertFalse(utils.is_path_windows('/unix/path'))
        self.assertFalse(utils.is_path_windows('/unix/path/file.nxs'))

    def test_path_separator(self):
        self.assertEqual(utils.path_separator('/unix/path'), '/')
        self.assertEqual(utils.path_separator('C:\\windows\\path'), '\\')

    def test_add_separator_to_end_of_dir_windows_dir_no_sep(self):
        self.assertEqual(utils.add_separator_to_end_of_directory('C:\\windows\\path'),
                         'C:\\windows\\path\\')

    def test_add_separator_to_end_of_dir_windows_dir_with_sep(self):
        self.assertEqual(utils.add_separator_to_end_of_directory('C:\\windows\\path\\'),
                         'C:\\windows\\path\\')

    def test_add_separator_to_end_of_dir_windows_file(self):
        self.assertEqual(utils.add_separator_to_end_of_directory('C:\\windows\\path\\file.nxs'),
                         'C:\\windows\\path\\file.nxs')

    def test_add_separator_to_end_of_dir_unix_dir_no_sep(self):
        self.assertEqual(utils.add_separator_to_end_of_directory('/unix/path'),
                         '/unix/path/')

    def test_add_separator_to_end_of_dir_unix_dir_with_sep(self):
        self.assertEqual(utils.add_separator_to_end_of_directory('/unix/path/'),
                         '/unix/path/')

    def test_add_separator_to_end_of_dir_unix_file(self):
        self.assertEqual(utils.add_separator_to_end_of_directory('/unix/path/file.nxs'),
                         '/unix/path/file.nxs')

    def test_add_to_windows_path(self):
        self.assertEqual(utils.add_to_path('C:\\windows', ['path', 'to', 'add', 'to']),
                         'C:\\windows\\path\\to\\add\\to')

    def test_add_to_unix_path(self):
        self.assertEqual(utils.add_to_path('/unix', ['path', 'to', 'add', 'to']),
                         '/unix/path/to/add/to')
