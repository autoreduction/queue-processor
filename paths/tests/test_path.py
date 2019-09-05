# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test the path class
"""
import unittest
import os

from mock import patch

from paths.path import Path, PathError

NOT_ABSOLUTE_FILE = 'not/absolute/path'
FILE_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(FILE_PATH)


# pylint:disable=missing-docstring
class TestPath(unittest.TestCase):

    def test_valid_init_for_file(self):
        path = Path('/test/path/file.nxs', 'file')
        self.assertEqual(path.type, 'file')
        self.assertEqual(path.value, '/test/path/file.nxs')
        self.assertEqual(path.validate_absolute, True)
        self.assertEqual(path.validate_exists, True)
        self.assertEqual(path.validate_readable, True)
        self.assertEqual(path.validate_type, True)
        self.assertEqual(path.validate_writable, False)

    def test_valid_init_for_dir(self):
        path = Path('/test/path/dir/', 'dir')
        self.assertEqual(path.type, 'directory')
        self.assertEqual(path.value, '/test/path/dir/')

    def test_valid_init_for_directory(self):
        path = Path('/test/path/dir/', 'directory')
        self.assertEqual(path.type, 'directory')
        self.assertEqual(path.value, '/test/path/dir/')

    def test_invalid_path_type(self):
        self.assertRaises(RuntimeError, Path, '/test/path/', 'invalid')

    def test_not_absolute_path(self):
        path = Path(NOT_ABSOLUTE_FILE, 'file')
        self.assertRaisesRegexp(PathError, "Path is not absolute", path.validate)

    def test_not_exist_path(self):
        path = Path(os.path.join(DIR_PATH, 'file_does_not_exist.nxs'), 'file')
        self.assertRaisesRegexp(PathError, "Path doesn't exist", path.validate)

    @patch('os.access')
    def test_not_readable_path(self, mock_access):
        mock_access.return_value = False
        path = Path(FILE_PATH, 'file')
        self.assertRaisesRegexp(PathError, "Path is not readable", path.validate)

    def test_not_file_validation(self):
        path = Path(DIR_PATH, 'file')
        self.assertRaisesRegexp(PathError, "Path is not a file", path.validate)

    def test_not_directory_validation(self):
        path = Path(FILE_PATH, 'dir')
        self.assertRaisesRegexp(PathError, "Path is not a directory", path.validate)

    def test_no_validation(self):
        path = Path('fake/path/directory', 'directory', False, False, False, False, False)
        self.assertTrue(path.validate())

    def test_path_equality_true(self):
        path1 = Path(FILE_PATH, 'file')
        path2 = Path(FILE_PATH, 'file')
        self.assertTrue(path1 == path2)

    def test_path_equality_mismatch_path_value(self):
        path1 = Path(FILE_PATH, 'file')
        path2 = Path(DIR_PATH, 'file')
        self.assertFalse(path1 == path2)

    def test_path_equality_mismatch_path_type(self):
        path1 = Path(FILE_PATH, 'file')
        path2 = Path(FILE_PATH, 'directory')
        self.assertFalse(path1 == path2)
