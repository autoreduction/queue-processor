# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for the PlotHandler class.
Currently tests:
initialisation of class parameters
construction of regular expression for looking up existing files
calling the SFTPClient with correct parameters
"""
import os
import unittest
from unittest.mock import Mock, patch
from parameterized import parameterized

from plotting.plot_handler import PlotHandler


# pylint:disable=line-too-long, protected-access
class TestPlotHandler(unittest.TestCase):
    """
    Test all the functionality of the PlotHandler
    """
    def setUp(self):
        """
        Create a few test PlotHandler objects
        """
        self.expected_file_extension_regex = '(png|jpg|bmp|gif|tiff)'
        self.expected_wish_data_filename = "WISH1234"
        self.expected_wish_file_regex = f"{self.expected_wish_data_filename}.*.{self.expected_file_extension_regex}"

        self.expected_mari_data_filename = "MARI1234"
        self.expected_mari_file_regex = f'{self.expected_mari_data_filename}.*.{self.expected_file_extension_regex}'
        self.input_data_filepath = "\\\\isis\\inst$\\NDXMARI\\Instrument\\data\\cycle_test\\MARI1234.nxs"
        self.mari_base = "/instrument/MARI/RBNumber/RB12345678/1234"
        self.expected_mari_rb_number = 12345678
        self.expected_mari_rb_folder = f"{self.mari_base}/autoreduced"

        self.test_plot_handler = PlotHandler(data_filepath=self.input_data_filepath,
                                             server_dir=self.expected_mari_rb_folder,
                                             rb_number=self.expected_mari_rb_number)

    def test_init(self):
        """
        Test: Class variables are initiated correctly
        When: PlotHandler is initialised
        """
        self.assertEqual(self.test_plot_handler.data_filename, self.expected_mari_data_filename)
        self.assertEqual(self.test_plot_handler.server_dir, self.expected_mari_rb_folder)
        self.assertEqual(self.test_plot_handler.file_extensions, ["png", "jpg", "bmp", "gif", "tiff"])
        self.assertEqual(self.test_plot_handler.rb_number, self.expected_mari_rb_number)

    def test_get_only_data_file_name(self):
        """
        Test: The parsing of the file is working as expected
        When: PlotHandler is initialised
        """
        self.assertEqual("MARI1234", self.test_plot_handler._get_only_data_file_name(self.input_data_filepath))
        self.assertEqual("MARI1234",
                         self.test_plot_handler._get_only_data_file_name(self.input_data_filepath.replace("\\", "/")))

    def test_generate_file_name_regex(self):
        """
        Test: Check that the correct regular expression for file look-up is created
        When: Valid instrument names are supplied to _generate_file_name_regex
        """
        param_list = [
            (self.expected_mari_data_filename, self.expected_mari_file_regex),
            (self.expected_wish_data_filename, self.expected_wish_file_regex),
        ]

        for expected_filename, expected_regex in param_list:
            self.test_plot_handler.data_filename = expected_filename
            actual = self.test_plot_handler._generate_file_name_regex()
            self.assertEqual(expected_regex, actual)

    def test_generate_file_extension_regex(self):
        """
        Test: Correct file extension pattern is generated
        When: _generate_file_extension_pattern() is called
        """
        expected_pattern = '.*.(png|jpg|bmp|gif|tiff)'
        actual_pattern = self.test_plot_handler._generate_file_extension_regex()
        self.assertEqual(expected_pattern, actual_pattern)

        self.test_plot_handler.file_extensions.append('txt')
        expected_pattern = '.*.(png|jpg|bmp|gif|tiff|txt)'
        actual_pattern = self.test_plot_handler._generate_file_extension_regex()
        self.assertEqual(expected_pattern, actual_pattern)

    @patch('plotting.plot_handler.os')
    def test_check_for_plot_files_path_exists(self, mock_os):
        """
        Test: sftpclient.get_filenames is called with the correct parameters if only one plot_type is used
        When: sftpclient.get_filenames is used to look for existing plot files
        """
        mock_os.path.exists.return_value = True
        mock_os.listdir.return_value = [
            "MARI1234_sometext_1.png", "MARI1234_sometext_2.png", "MARI1234.nxs", "MARI1234_sometext.nxs"
        ]

        # check that only the valid matches have been found
        assert mock_os.listdir.return_value[0:2] == self.test_plot_handler._check_for_plot_files()

    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files')
    @patch('plotting.plot_handler.shutil.copy')
    def test_get_plot_files(self, mock_copy: Mock, mock_find_files):
        """
        Test: get_plot_files returns the expected plot files
        When: called with valid arguments and files exist on server and none exist locally
        """
        expected_files = ['expected.png']
        mock_find_files.return_value = expected_files
        expected_local = os.path.join(self.test_plot_handler.static_graph_dir, expected_files[0])
        expected_server = os.path.join(self.expected_mari_rb_folder, expected_files[0])

        actual_path = self.test_plot_handler.get_plot_file()
        mock_copy.assert_called_once_with(expected_server, expected_local)
        self.assertEqual([f'/static/graphs/{expected_files[0]}'], actual_path)

    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files')
    @patch('plotting.plot_handler.shutil.copy')
    def test_get_plot_files_multiple(self, mock_copy: Mock, mock_find_files):
        """
        Test: Multiple file paths are returned as a list
        When: Multiple image files exist on the server relating to the same run and none exist
        locally
        """
        expected_files = ['expected_1.png', 'expected_2.png']
        mock_find_files.return_value = expected_files

        expected_paths = [f'/static/graphs/{expected_files[0]}', f'/static/graphs/{expected_files[1]}']

        actual_paths = self.test_plot_handler.get_plot_file()
        self.assertEqual(mock_copy.call_count, len(expected_files))
        self.assertEqual(expected_paths, actual_paths)

    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files', return_value=[])
    def test_get_plot_file_none_found(self, mock_cfpl: Mock):
        """
        Test: None is returned
        When: No files can be found on the server or locally
        """
        self.assertIsNone(self.test_plot_handler.get_plot_file())
        mock_cfpl.assert_called_once()

    @parameterized.expand([[FileNotFoundError, "does not exist"], [PermissionError, "Insufficient permissions"]])
    @patch('plotting.plot_handler.LOGGER')
    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files')
    @patch('plotting.plot_handler.shutil.copy')
    def test_get_plot_files_cant_download_none_local(
        self,
        exc_type: Exception,
        expected_log_message: str,
        mock_copy: Mock,
        mock_find_files,
        mock_logger,
    ):
        """
        Test: get_plot_files returns the expected plot files
        When: called with valid arguments and files exist on server and not locally
        """
        expected_files = ['expected.png']
        mock_find_files.return_value = expected_files
        mock_copy.side_effect = exc_type
        assert not self.test_plot_handler.get_plot_file()
        mock_logger.error.assert_called_once()
        assert expected_log_message in mock_logger.error.call_args[0][0]
        assert self.mari_base in mock_logger.error.call_args[0][1]


if __name__ == '__main__':
    unittest.main()
