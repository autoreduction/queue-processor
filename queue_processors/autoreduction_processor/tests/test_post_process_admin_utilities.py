# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for post process helper functionality
"""
import contextlib
import unittest
import io

from pathlib import PosixPath
from mock import patch, MagicMock

from queue_processors.autoreduction_processor.post_process_admin_utilities import \
    windows_to_linux_path, channels_redirected


# pylint:disable=missing-docstring,invalid-name,protected-access,no-self-use,too-many-arguments
class TestPostProcessAdminHelpers(unittest.TestCase):
    DIR = "queue_processors.autoreduction_processor"

    def test_windows_to_linux_data_path(self):
        """
        Test:
        When:
        """
        windows_path = "\\\\isis\\inst$\\some\\more\\path.nxs"
        actual = windows_to_linux_path(windows_path, '')
        self.assertEqual(actual, '/isis/some/more/path.nxs')

    def test_windows_to_linux_autoreduce_path(self):
        """
        Test:
        When:
        """
        windows_path = "\\\\autoreduce\\data\\some\\more\\path.nxs"
        actual = windows_to_linux_path(windows_path, '/temp')
        self.assertEqual(actual, '/temp/data/some/more/path.nxs')

    @patch('os.path.isfile')
    @patch(f"{DIR}.post_process_admin.PostProcessAdmin.specify_instrument_directories")
    @patch(f"{DIR}.post_process_admin.PostProcessAdmin.create_log_path")
    def test_channels_redirect(self, mock_clp, mock_iod,  mock_is_file):
        """
        Test: A context manager is returned
        When: Called
        """

        mock_is_file.return_value = True

        file_name = "test.log"
        log_directory = f"{mock_iod}/reduction_log/"
        log_and_error_name = "RB_1234_Run_4321_"

        script_out = PosixPath(f"{log_directory}{log_and_error_name}{'Script.out'}")
        mantid_out = PosixPath(f"{log_directory}{log_and_error_name}{'Mantid.log'}")
        out_stream = io.StringIO()

        actual = channels_redirected(out_file=script_out,
                                     err_file=mantid_out,
                                     out_stream=out_stream)
        self.assertIsInstance(actual, contextlib._GeneratorContextManager)
        print(actual.__dict__)

