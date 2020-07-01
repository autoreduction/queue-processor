# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test path setup is correct in ISISReductionPathManager
"""
import os
import unittest

from mock import patch

from paths.isis.isis_reduction_path_manager import ISISReductionPathManager
from paths.path_manipulation import append_path, split
from queue_processors.autoreduction_processor.settings import MISC


# pylint:disable=missing-docstring
class TestISISReductionPathManager(unittest.TestCase):

    @patch('paths.path.Path.validate')
    def test_valid_init(self, mock_validate):
        """
        Create expected paths from AutoreductionProcessor.settings.MISC and test that
        the paths in the ISISReductionPathManager are set up correctly to match these

        Validation is tested somewhere else so we can mock it here instead
        """
        mock_validate.return_value = True
        isis_paths = ISISReductionPathManager(input_data_path=os.path.realpath(__file__),
                                              instrument='GEM',
                                              proposal='12345',
                                              run_number='54321')
        # Input Paths
        expected_data_path = os.path.realpath(__file__)
        expected_script_path = append_path(MISC['scripts_directory'] % 'GEM', ['reduce.py'])
        expected_vars_path = append_path(MISC['scripts_directory'] % 'GEM', ['reduce_vars.py'])
        self.assertEqual(expected_data_path, isis_paths.input_paths.data_path.value)
        self.assertEqual(expected_script_path, isis_paths.input_paths.reduction_script_path.value)
        self.assertEqual(expected_vars_path, isis_paths.input_paths.reduction_variables_path.value)

        # Output Paths
        expected_out_path = MISC['ceph_directory'] % ('GEM', '12345', '54321')
        expected_log_path = append_path(MISC['ceph_directory'] % ('GEM', '12345', '54321'),
                                        ['reduction_log'])
        self.assertEqual(expected_out_path, isis_paths.output_paths.data_directory.value)
        self.assertEqual(expected_log_path, isis_paths.output_paths.log_directory.value)

        # Temporary Paths
        expected_temp_path = MISC['temp_root_directory']
        expected_temp_out_path = append_path(expected_temp_path, split(expected_out_path))
        expected_temp_log_path = append_path(expected_temp_path, split(expected_log_path))
        self.assertEqual(expected_temp_path, isis_paths.temporary_paths.root_directory.value)
        self.assertEqual(expected_temp_out_path, isis_paths.temporary_paths.data_directory.value)
        self.assertEqual(expected_temp_log_path, isis_paths.temporary_paths.log_directory.value)
