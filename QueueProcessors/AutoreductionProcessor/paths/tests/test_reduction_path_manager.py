"""
Tests for reduction path manager functions as expected
"""
import unittest
import tempfile

from mock import patch

from QueueProcessors.AutoreductionProcessor.paths.reduction_path_manager import (ReductionPathManager,
                                                                                 ReductionPathError)


class TestReductionPathManager(unittest.TestCase):

    def setUp(self):
        self.test_file = tempfile.NamedTemporaryFile(suffix='.nxs', delete=False).name
        self.test_dir = tempfile.mkdtemp()

    @patch('QueueProcessors.AutoreductionProcessor.paths.reduction_path_manager.ReductionPathManager.validate_paths')
    def test_init(self, _):
        """ Ensure all vriables are assigned correctly """
        path_manager = ReductionPathManager('/input_file.py',
                                            '/reduction/script.py',
                                            '/reduction/variables.py',
                                            '/temporary/dir/',
                                            '/output/dir/')
        self.assertEqual(path_manager.input_data_file_path, '/input_file.py')
        self.assertEqual(path_manager.reduction_script_file_path, '/reduction/script.py')
        self.assertEqual(path_manager.reduction_script_variables_file_path,
                         '/reduction/variables.py')
        self.assertEqual(path_manager.temporary_output_directory, '/temporary/dir/')
        self.assertEqual(path_manager.final_output_directory, '/output/dir/')
        self.assertEqual(path_manager.final_output_log_directory, '/output/dir/reduction_log/')

    @patch('QueueProcessors.AutoreductionProcessor.paths.reduction_path_manager.ReductionPathManager.validate_paths')
    def test_add_log_dir_windows_no_trailing_slash(self, _):
        path_manager = ReductionPathManager('', '', '', '', '\\test')
        self.assertEqual(path_manager.final_output_log_directory, '\\test\\reduction_log\\')

    @patch('QueueProcessors.AutoreductionProcessor.paths.reduction_path_manager.ReductionPathManager.validate_paths')
    def test_add_log_dir_windows_trailing_slash(self, _):
        path_manager = ReductionPathManager('', '', '', '', '\\test\\')
        self.assertEqual(path_manager.final_output_log_directory, '\\test\\reduction_log\\')

    @patch('QueueProcessors.AutoreductionProcessor.paths.reduction_path_manager.ReductionPathManager.validate_paths')
    def test_add_log_dir_linux_no_trailing_slash(self, _):
        path_manager = ReductionPathManager('', '', '', '', '/test')
        self.assertEqual(path_manager.final_output_log_directory, '/test/reduction_log/')

    @patch('QueueProcessors.AutoreductionProcessor.paths.reduction_path_manager.ReductionPathManager.validate_paths')
    def test_add_log_dir_linux_trailing_slash(self, _):
        path_manager = ReductionPathManager('', '', '', '', '/test/')
        self.assertEqual(path_manager.final_output_log_directory, '/test/reduction_log/')

    def test_invalid_files(self):
        self.assertRaisesRegexp(ReductionPathError, 'Doesn\'t exist', ReductionPathManager,
                                'unreachable', '', '', '', '')

    def test_invalid_directory(self):
        self.assertRaisesRegexp(ReductionPathError, 'Doesn\'t exist', ReductionPathManager,
                                self.test_file, self.test_file, self.test_file, 'unreachable',
                                'unreachable')

    @patch('QueueProcessors.AutoreductionProcessor.paths.reduction_path_manager.ReductionPathManager._add_log_dir_to_output_path')
    def test_invalid_file_as_directory(self, mock_log_dir):
        mock_log_dir.return_value = self.test_file
        self.assertRaisesRegexp(ReductionPathError, 'Not directory', ReductionPathManager,
                                self.test_file, self.test_file, self.test_file, self.test_file,
                                self.test_file)

    def test_directory_as_file(self):
        self.assertRaisesRegexp(ReductionPathError, 'Not file', ReductionPathManager,
                                self.test_dir, self.test_dir, self.test_dir, self.test_dir,
                                self.test_dir)
