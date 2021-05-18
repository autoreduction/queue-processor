# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import contextlib
import io
import unittest
from pathlib import Path

from unittest.mock import patch

from autoreduce_qp.queue_processor.reduction.utilities import windows_to_linux_path, channels_redirected


class TestReductionRunnerHelpers(unittest.TestCase):
    def test_windows_to_linux_data_path(self):
        """
        Test: Windows to linux path is correctly modified to linux format
        When: Called with a windows formatted path.
        """
        windows_path = "\\\\isis\\inst$\\some\\more\\path.nxs"
        actual = windows_to_linux_path(windows_path, '')
        self.assertEqual(actual, '/isis/some/more/path.nxs')

    def test_windows_to_linux_autoreduce_path(self):
        """
        Test: Linux path is correctly constructed from concatenating temp path and windows path
        When: Called with windows path and temporary path
        """
        windows_path = "\\\\autoreduce\\data\\some\\more\\path.nxs"
        actual = windows_to_linux_path(windows_path, '/temp')
        self.assertEqual(actual, '/temp/data/some/more/path.nxs')

    @patch('os.path.isfile')
    def test_channels_redirect(self, mock_is_file):
        """
        Test: A context manager is returned
        When: Called
        """
        mock_is_file.return_value = True
        log_directory = "/reduction_log/"
        log_and_error_name = "RB_1234_Run_4321_"

        script_out = Path(f"{log_directory}{log_and_error_name}{'Script.out'}")
        mantid_out = Path(f"{log_directory}{log_and_error_name}{'Mantid.log'}")
        out_stream = io.StringIO()

        actual = channels_redirected(out_file=script_out, error_file=mantid_out, out_stream=out_stream)
        self.assertIsInstance(actual, contextlib._GeneratorContextManager)  # pylint:disable=protected-access
