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
from mock import patch, call

from plotting.plot_handler import PlotHandler
from utils.project.structure import get_project_root


# pylint:disable=line-too-long, protected-access
class TestPlotHandler(unittest.TestCase):
    """
    Test all the functionality of the PlotHandler
    """
    # pylint:disable=too-many-instance-attributes
    def setUp(self):
        """
        Create a few test PlotHandler objects
        """
        self.expected_mari_instrument_name = "MARI"
        self.expected_mari_rb_number = 12345678
        self.expected_mari_run_number = 1234
        self.expected_mari_rb_folder = "/instrument/MARI/RBNumber/RB12345678/1234/autoreduced/"
        self.test_plot_handler = PlotHandler(instrument_name=self.expected_mari_instrument_name,
                                             rb_number=self.expected_mari_rb_number,
                                             run_number=self.expected_mari_run_number,
                                             server_dir=self.expected_mari_rb_folder)

        self.expected_static_graph_dir = os.path.join(get_project_root(), 'WebApp',
                                                      'autoreduce_webapp', 'static',
                                                      'graphs')

    def test_init(self):
        """
        Test: Class variables are initiated correctly
        When: PlotHandler is initialised
        """
        self.assertEqual(self.test_plot_handler.instrument_name, self.expected_mari_instrument_name)
        self.assertEqual(self.test_plot_handler.run_number, self.expected_mari_run_number)
        self.assertEqual(self.test_plot_handler.server_dir, self.expected_mari_rb_folder)
        self.assertEqual(self.test_plot_handler.file_extensions, ["png", "jpg", "bmp", "gif", "tiff"])
        self.assertEqual(self.test_plot_handler.rb_number, self.expected_mari_rb_number)
        self.assertEqual(self.test_plot_handler.static_graph_dir, self.expected_static_graph_dir)

    def test_regexp_for_file(self):
        """
        Test: Check that the correct regular expression for file look-up is created
        When: Valid instrument names are supplied to _generate_file_name_regex
        """
        expected_mari = "MAR(I)?1234.*.png"
        actual = self.test_plot_handler._generate_file_name_regex('png')
        self.assertEqual(expected_mari, actual)
        expected_wish = "WISH1234.*.tiff"
        self.test_plot_handler.instrument_name = "WISH"
        actual = self.test_plot_handler._generate_file_name_regex('tiff')
        self.assertEqual(expected_wish, actual)

    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.get_filenames')
    def test_check_for_plot_files(self, mock_get_filenames, mock_client_init):
        """
        Test: sftpclient.get_filenames is called with the correct parameters if only one plot_type is used
        When: sftpclient.get_filenames is used to look for existing plot files
        """
        self.test_plot_handler._check_for_plot_files()
        mock_client_init.assert_called_once()
        expected_calls = [
            call(server_dir_path=self.expected_mari_rb_folder, regex="MAR(I)?1234.*.png"),
            call(server_dir_path=self.expected_mari_rb_folder, regex="MAR(I)?1234.*.jpg"),
            call(server_dir_path=self.expected_mari_rb_folder, regex="MAR(I)?1234.*.bmp"),
            call(server_dir_path=self.expected_mari_rb_folder, regex="MAR(I)?1234.*.gif"),
            call(server_dir_path=self.expected_mari_rb_folder, regex="MAR(I)?1234.*.tiff")
        ]
        mock_get_filenames.assert_has_calls(expected_calls, any_order=True)

    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files')
    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.retrieve')
    def test_get_plot_files(self, mock_retrieve, mock_client_init, mock_find_files):
        """
        Test: get_plot_files returns the expected plot files
        When: called with valid arguments and files exist
        """
        expected_files = ['expected.png']
        mock_find_files.return_value = expected_files
        expected_local = os.path.join(self.expected_static_graph_dir, expected_files[0])
        expected_server = self.expected_mari_rb_folder + expected_files[0]

        actual_path = self.test_plot_handler.get_plot_file()
        mock_client_init.assert_called_once()
        mock_retrieve.assert_called_once_with(
            server_file_path=expected_server, local_file_path=expected_local, override=True)
        self.assertEqual(f'/static/graphs/{expected_files[0]}', actual_path)

    # pylint:disable=unnecessary-pass
    def test_construct_plot(self):
        """
        Test:
        When:
        """
        pass
