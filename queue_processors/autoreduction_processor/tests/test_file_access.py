"""
Test file access checks
"""
import unittest
import os
import stat

from mock import patch
import tempfile

import queue_processors.autoreduction_processor.file_access as file_access


class TestFileAccess(unittest.TestCase):

    def test_exist_raise_permissions_exception(self):
        self.assertRaises(file_access.PermissionException, file_access.check_exists, 'fake/path')

    @patch('os.path.isdir', return_value=False)
    @patch('os.makedirs')
    def test_create_dir_when_dir_not_exist(self, mock_makedirs, _):
        file_access.create_dir_if_does_not_exist('fake/path')
        self.assertTrue(mock_makedirs.called)

    @patch('os.path.isdir', return_value=True)
    @patch('os.makedirs')
    def test_create_dir_when_dir_does_exist(self, mock_makedirs, _):
        file_access.create_dir_if_does_not_exist('fake/path')
        self.assertFalse(mock_makedirs.called)

    #def test_read_raise_permissions_exception(self):
    #    with tempfile.TemporaryFile() as tmp_file:
    #        path = tmp_file.name
    #        os.chmod(path, 000)
    #        self.assertRaises(file_access.PermissionException, file_access.check_read, path)

    #def test_write_raise_permissions_exception(self):
    #def test_exist_valid(self):
    #def test_read_valid(self):
    #def test_write_valid(self):
