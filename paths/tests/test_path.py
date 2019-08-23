import unittest
import os

from paths.path import Path, PathError

NOT_ABSOLUTE_FILE = 'not/absolute/path'
FILE_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(FILE_PATH)


class TestPath(unittest.TestCase):

    def test_valid_init_for_file(self):
        path = Path('/test/path/file.nxs', 'file')
        self.assertEqual(path.type, 'file')
        self.assertEqual(path.value, '/test/path/file.nxs')

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
        self.assertRaisesRegexp(PathError, "Path is not absolute", path.validate_path)

    def test_not_exist_path(self):
        path = Path(os.path.join(DIR_PATH, 'file_does_not_exist.nxs'), 'file')
        self.assertRaisesRegexp(PathError, "Path doesn't exist", path.validate_path)

    def test_not_file_validation(self):
        path = Path(DIR_PATH, 'file')
        self.assertRaisesRegexp(PathError, "Path is not a file", path.validate_path)

    def test_not_directory_validation(self):
        path = Path(FILE_PATH, 'dir')
        self.assertRaisesRegexp(PathError, "Path is not a directory", path.validate_path)
