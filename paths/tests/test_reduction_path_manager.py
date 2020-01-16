# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for reduction path manager functions as expected
"""
import unittest
import tempfile

from mock import patch

from paths.reduction_path_manager import (ReductionPathManager)


# pylint:disable=missing-docstring
class TestReductionPathManager(unittest.TestCase):

    def setUp(self):
        self.test_file = tempfile.NamedTemporaryFile(suffix='.nxs', delete=False).name
        self.test_dir = tempfile.mkdtemp()

    @patch('paths.path.Path.validate')
    def test_init(self, _):
        """ Ensure all variables are assigned correctly """

        path_manager = ReductionPathManager('/input_file.py',
                                            '/reduction/script.py',
                                            '/reduction/variables.py',
                                            '/temporary/dir/',
                                            '/output/dir/')
        # Input files
        self.assertEqual(path_manager.input_paths.data_path.value, '/input_file.py')
        self.assertEqual(path_manager.input_paths.reduction_script_path.value,
                         '/reduction/script.py')
        self.assertEqual(path_manager.input_paths.reduction_variables_path.value,
                         '/reduction/variables.py')

        # Temporary files
        self.assertEqual(path_manager.temporary_paths.root_directory.value, '/temporary/dir/')
        self.assertEqual(path_manager.temporary_paths.data_directory.value,
                         '/temporary/dir/output/dir/')
        self.assertEqual(path_manager.temporary_paths.log_directory.value,
                         '/temporary/dir/output/dir/reduction_log/')

        # Output files
        self.assertEqual(path_manager.output_paths.data_directory.value, '/output/dir/')
        self.assertEqual(path_manager.output_paths.log_directory.value,
                         '/output/dir/reduction_log/')
