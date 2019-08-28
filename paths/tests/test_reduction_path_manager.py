"""
Tests for reduction path manager functions as expected
"""
import unittest
import tempfile

from mock import patch

from paths.path import Path
from paths.reduction_path_manager import (ReductionPathManager)


class TestReductionPathManager(unittest.TestCase):

    def setUp(self):
        self.test_file = tempfile.NamedTemporaryFile(suffix='.nxs', delete=False).name
        self.test_dir = tempfile.mkdtemp()

    @patch('paths.reduction_path_manager.ReductionPathManager.validate_paths')
    def test_init(self, _):
        """ Ensure all variables are assigned correctly """
        path_manager = ReductionPathManager('/input_file.py',
                                            '/reduction/script.py',
                                            '/reduction/variables.py',
                                            '/temporary/dir/',
                                            '/output/dir/')
        # Input files
        self.assertEqual(path_manager.input_paths.data_path, Path('/input_file.py', 'file'))
        self.assertEqual(path_manager.input_paths.reduction_script_path,
                         Path('/reduction/script.py', 'file'))
        self.assertEqual(path_manager.input_paths.reduction_script_path,
                         Path('/reduction/variables.py', 'file'))

        # Temporary files
        self.assertEqual(path_manager.temporary_paths.root_directory,
                         Path('/temporary/dir/', 'directory'))
        self.assertEqual(path_manager.temporary_paths.data_directory,
                         Path('/temporary/dir/', 'directory'))
        self.assertEqual(path_manager.temporary_paths.log_directory,
                         Path('/temporary/dir/', 'directory'))

        # Output files
        self.assertEqual(path_manager.output_paths.data_directory,
                         Path('/output/dir/', 'directory'))
        self.assertEqual(path_manager.output_paths.log_directory,
                         Path('/output/dir/reduction_log/', 'directory'))
