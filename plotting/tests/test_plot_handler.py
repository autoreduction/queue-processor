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
from unittest.mock import patch

from plotting.plot_handler import PlotHandler
from utils.project.structure import get_project_root


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
        self.expected_mari_rb_number = 12345678
        self.expected_mari_rb_folder = "/instrument/MARI/RBNumber/RB12345678/1234/autoreduced"

        self.test_plot_handler = PlotHandler(data_filepath=self.input_data_filepath,
                                             server_dir=self.expected_mari_rb_folder,
                                             rb_number=self.expected_mari_rb_number)

        self.expected_static_graph_dir = os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp', 'static',
                                                      'graphs')

    def test_init(self):
        """
        Test: Class variables are initiated correctly
        When: PlotHandler is initialised
        """
        self.assertEqual(self.test_plot_handler.data_filename, self.expected_mari_data_filename)
        self.assertEqual(self.test_plot_handler.server_dir, self.expected_mari_rb_folder)
        self.assertEqual(self.test_plot_handler.file_extensions, ["png", "jpg", "bmp", "gif", "tiff"])
        self.assertEqual(self.test_plot_handler.rb_number, self.expected_mari_rb_number)
        self.assertEqual(self.test_plot_handler.static_graph_dir, self.expected_static_graph_dir)

    def test_get_only_data_file_name(self):
        """
        Test: The parsing of the file is working as expected
        When: PlotHandler is initialised
        """
        self.assertEqual("MARI1234", self.test_plot_handler._get_only_data_file_name(self.input_data_filepath))

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

    @patch("os.listdir", return_value=["MARI1234_123.456.png", "MARI1234_124.png", "MARI123.nxs"])
    @patch("plotting.plot_handler.PlotHandler._generate_file_name_regex")
    def test_get_plot_files_locally_files_exist_returns_list(self, mock_gfn_regex, mock_listdir):
        """
        Test: Correct file paths are returned
        When: Multiple matching files exist
        """
        mock_gfn_regex.return_value = self.expected_mari_file_regex

        expected_files = ["/static/graphs/MARI1234_123.456.png", "/static/graphs/MARI1234_124.png"]
        actual = self.test_plot_handler._get_plot_files_locally()
        self.assertEqual(expected_files, actual)

        mock_listdir.assert_called()
        mock_gfn_regex.assert_called()

    @patch("os.listdir", return_value=["MARI1234.png"])
    @patch("plotting.plot_handler.PlotHandler._generate_file_name_regex")
    def test_get_plot_files_locally_single_file_returns_list(self, mock_gfn_regex, mock_listdir):
        """
        Test: Correct file path is returned
        When: Single matching file exists
        """
        mock_gfn_regex.return_value = self.expected_mari_file_regex

        expected_files = ["/static/graphs/MARI1234.png"]
        actual = self.test_plot_handler._get_plot_files_locally()
        self.assertEqual(expected_files, actual)

        mock_listdir.assert_called()
        mock_gfn_regex.assert_called()

    @patch("os.listdir", return_value=["MARI1234.nxs"])
    @patch("plotting.plot_handler.PlotHandler._generate_file_name_regex")
    def test_get_plot_files_no_matching_file_returns_empty_list(self, mock_gfn_regex, mock_listdir):
        """
        Test: Empty list is returned
        When: No matching file exists
        """
        mock_gfn_regex.return_value = self.expected_mari_file_regex

        expected_files = []
        actual = self.test_plot_handler._get_plot_files_locally()
        self.assertEqual(expected_files, actual)

        mock_listdir.assert_called()
        mock_gfn_regex.assert_called()

    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.get_filenames')
    def test_check_for_plot_files(self, mock_get_filenames, mock_client_init):
        """
        Test: sftpclient.get_filenames is called with the correct parameters if only one plot_type is used
        When: sftpclient.get_filenames is used to look for existing plot files
        """
        self.test_plot_handler._check_for_plot_files()
        mock_client_init.assert_called_once()
        mock_get_filenames.assert_called_once_with(server_dir_path=self.expected_mari_rb_folder,
                                                   regex=self.expected_mari_file_regex)

    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files')
    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.retrieve')
    @patch("plotting.plot_handler.PlotHandler._get_plot_files_locally", return_value=[])
    def test_get_plot_files_no_local_files(self, mock_gpfl, mock_retrieve, mock_client_init, mock_find_files):
        """
        Test: get_plot_files returns the expected plot files
        When: called with valid arguments and files exist on server and none exist locally
        """
        expected_files = ['expected.png']
        mock_find_files.return_value = expected_files
        expected_local = os.path.join(self.expected_static_graph_dir, expected_files[0])
        expected_server = os.path.join(self.expected_mari_rb_folder, expected_files[0])

        actual_path = self.test_plot_handler.get_plot_file()
        mock_client_init.assert_called_once()
        mock_retrieve.assert_called_once_with(server_file_path=expected_server,
                                              local_file_path=expected_local,
                                              override=True)
        self.assertEqual([f'/static/graphs/{expected_files[0]}'], actual_path)

        mock_gpfl.assert_called()

    @patch('utils.clients.sftp_client.SFTPClient.retrieve')
    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files')
    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch("plotting.plot_handler.PlotHandler._get_plot_files_locally", return_value=[])
    def test_get_plot_files_multiple_none_local(self, mock_gpfl, mock_client_init, mock_find_files, _):
        """
        Test: Multiple file paths are returned as a list
        When: Multiple image files exist on the server relating to the same run and none exist
        locally
        """
        expected_files = ['expected_1.png', 'expected_2.png']
        mock_find_files.return_value = expected_files

        expected_paths = [f'/static/graphs/{expected_files[0]}', f'/static/graphs/{expected_files[1]}']

        actual_paths = self.test_plot_handler.get_plot_file()
        mock_client_init.assert_called_once()  # Ensure this is not initialised more than once
        self.assertEqual(expected_paths, actual_paths)

        mock_gpfl.assert_called()

    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files', return_value=[])
    @patch("plotting.plot_handler.PlotHandler._get_plot_files_locally", return_value=[])
    def test_get_plot_file_none_found(self, mock_gpfl, _):
        """
        Test: None is returned
        When: No files can be found on the server or locally
        """
        self.assertIsNone(self.test_plot_handler.get_plot_file())
        mock_gpfl.assert_called()

    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files')
    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.retrieve')
    @patch("plotting.plot_handler.PlotHandler._get_plot_files_locally", return_value=[])
    def test_get_plot_files_cant_download_none_local(self, mock_gpfl, mock_retrieve, mock_client_init, mock_find_files):
        """
        Test: get_plot_files returns the expected plot files
        When: called with valid arguments and files exist on server and not locally
        """
        expected_files = ['expected.png']
        mock_find_files.return_value = expected_files
        mock_retrieve.side_effect = RuntimeError
        self.assertIsNone(self.test_plot_handler.get_plot_file())
        mock_gpfl.assert_called()
        mock_client_init.assert_called_once()

    @patch("plotting.plot_handler.PlotHandler._check_for_plot_files")
    @patch("plotting.plot_handler.PlotHandler._get_plot_files_locally")
    def test_get_plot_file_from_local_storage(self, mock_gpfl, mock_cfpf):
        """
        Test: Correct files returned from local storage
        When: When files exist already exist locally
        """
        mock_gpfl.return_value = ["/static/graphs/expected.png"]

        expected = ["/static/graphs/expected.png"]
        actual = self.test_plot_handler.get_plot_file()
        self.assertEqual(expected, actual)

        mock_gpfl.assert_called()
        mock_cfpf.assert_not_called()


if __name__ == '__main__':
    unittest.main()
