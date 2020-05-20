# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import unittest
from mock import patch

from plotting.plot_handler import PlotHandler


class TestPlotHandler(unittest.TestCase):
    """
    Test all the functionality of the PlotHandler
    """

    def setUp(self):
        """
        Create a few test PlotHandler objects
        """
        self.test_MARI_png_plottype = PlotHandler(instrument_name="MARI", rb_number=12345678, run_number=1234,
                                                  plot_type="png")
        self.test_WISH_None_plottype = PlotHandler(instrument_name="WISH", rb_number=87654321, run_number=4321)

    def test_init_MARI_png_plottype(self):
        """
        Test: Class variables are initiated correctly when instrument name is MARI and "png" is passed as plot type
        When: PlotHandler is initialised
        """
        self.assertEqual(self.test_MARI_png_plottype.instrument_name, "MARI")
        self.assertEqual(self.test_MARI_png_plottype.rb_number, 12345678)
        self.assertEqual(self.test_MARI_png_plottype.run_number, 1234)
        self.assertEqual(self.test_MARI_png_plottype.plot_type, ["png"])
        self.assertEqual(self.test_MARI_png_plottype._RBfolder,
                         "/instrument/MARI/RBNumber/RB12345678/1234/autoreduced/")
        self.assertEqual(self.test_MARI_png_plottype._existing_plot_files, [])

    def test_init_WISH_None_plottype(self):
        """
        Test: Class variables are initialised correctly when instrument name is WISH and no plot type is passed
        When: PlotHandler is initialised
        """
        self.assertEqual(self.test_WISH_None_plottype.instrument_name, "WISH")
        self.assertEqual(self.test_WISH_None_plottype.rb_number, 87654321)
        self.assertEqual(self.test_WISH_None_plottype.run_number, 4321)
        self.assertEqual(self.test_WISH_None_plottype.plot_type, ["png", "jpg", "bmp", "gif", "tiff"])
        self.assertEqual(self.test_WISH_None_plottype._RBfolder,
                         "/instrument/WISH/RBNumber/RB87654321/4321/autoreduced/")
        self.assertEqual(self.test_WISH_None_plottype._existing_plot_files, [])

    def test_regexp_for_file_name_MARI_png_plottype(self):
        """
        Test: Check that the correct regular expression for file look-up is created
        When: Instrument name is MARI and a single plot type is passed to the class
        """
        expected = "MAR[I]1234*.png"
        actual = self.test_MARI_png_plottype._regexp_for_file_name(self.test_MARI_png_plottype.plot_type[0])
        self.assertEqual(expected, actual)

    def test_regexp_for_file_name_WISH_None_plottype(self):
        """
        Test: Check that the correct regular expression for file look-up is created
        When: Instrument name is WISH and no plot type is passed to the class
        """
        expected = "WISH4321*.jpg"
        actual = self.test_WISH_None_plottype._regexp_for_file_name(self.test_WISH_None_plottype.plot_type[1])
        self.assertEqual(expected, actual)
        expected = "WISH4321*.tiff"
        actual = self.test_WISH_None_plottype._regexp_for_file_name(self.test_WISH_None_plottype.plot_type[-1])
        self.assertEqual(expected, actual)

    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.get_filenames')
    def test_check_for_plot_files_MARI_png_plottype(self, mock_get_filenames, mock_client_init):
        """
        Test: sftpclient.get_filenames is called with the correct parameters if only one plot_type is used
        When: sftpclient.get_filenames is used to look for existing plot files
        :return:
        """
        self.test_MARI_png_plottype._check_for_plot_files()
        #client = SFTPClient()
        mock_client_init.assert_called_once()
        mock_get_filenames.assert_called_once_with(server_dir_path="/instrument/MARI/RBNumber/RB12345678/1234/autoreduced/", regex="MAR[I]1234*.png")

    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.get_filenames')
    def test_check_for_plot_files_WISH_None_plottype(self, mock_get_filenames, mock_client_init):
        """
        Test: sftpclient.get_filenames is called with the correct parameters when multiple plot_types are used
        When: sftpclient.get_filenames is used to look for existing plot files
        :return:
        """
        self.test_WISH_None_plottype._check_for_plot_files()
        mock_client_init.assert_called_once()
        # check number of times the sftpclient.get_filenames method was called
        expected=5
        actual=mock_get_filenames.call_count
        self.assertEqual(expected,actual)
        # check that the sftpclient.get_filenames method was called with the right parameters
        mock_get_filenames.assert_any_call(server_dir_path="/instrument/WISH/RBNumber/RB87654321/4321/autoreduced/", regex="WISH4321*.png")
        mock_get_filenames.assert_any_call(server_dir_path="/instrument/WISH/RBNumber/RB87654321/4321/autoreduced/", regex="WISH4321*.jpg")
        mock_get_filenames.assert_any_call(server_dir_path="/instrument/WISH/RBNumber/RB87654321/4321/autoreduced/", regex="WISH4321*.bmp")
        mock_get_filenames.assert_any_call(server_dir_path="/instrument/WISH/RBNumber/RB87654321/4321/autoreduced/", regex="WISH4321*.gif")
        mock_get_filenames.assert_any_call(server_dir_path="/instrument/WISH/RBNumber/RB87654321/4321/autoreduced/", regex="WISH4321*.tiff")

    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.get_filenames', return_value=["existing_file.png"])
    @patch('utils.clients.sftp_client.SFTPClient.retrieve')
    def test_get_plot_file_MARI_png_plottype_1_file_found(self, mock_retrieve, mock_get_filenames, mock_client_init):
        """
        Test: sftpclient.retrieve is called with the correct parameter if one existing files has been found
        When: sftpclient.retrieve is used to retrieve an existing plot file
        """
        # call the get_plot_file method
        self.test_MARI_png_plottype.get_plot_file()
        # check that the found file name is saved correctly
        self.assertEqual(self.test_MARI_png_plottype._existing_plot_files,["existing_file.png"])
        # check that the sftpclients methods were called as expected
        mock_get_filenames.assert_called_once()
        mock_retrieve.assert_called_once()
        # check that the sftpclient.retrieve method was called with the correct parameters
        mock_retrieve.assert_called_once_with(server_path="/instrument/MARI/RBNumber/RB12345678/1234/autoreduced/existing_file.png", local_path=None, override=True)


    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('plotting.plot_handler.PlotHandler.__init__', return_value=None)
    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files', return_value=["existing_file.png", "existing_file.jpg"])
    @patch('utils.clients.sftp_client.SFTPClient.retrieve')
    def test_get_plot_file_WISH_None_plottype_2_files_found(self, mock_retrieve, mock_check_for_plot_files, mock_plothandler_init, mock_client_init):
        """
        Test: sftpclient.retrieve is called with the correct parameter if two existing files have been found
        When: sftpclient.retrieve is used to retrieve an existing plot file
        """
        # call the get_plot_file method
        self.test_WISH_None_plottype.get_plot_file()
        # check that the found file names are saved correctly
        self.assertEqual(self.test_WISH_None_plottype._existing_plot_files,["existing_file.png", "existing_file.jpg"])
        # check that the two mocked methods were called as expected
        mock_check_for_plot_files.assert_called_once()
        mock_retrieve.assert_called_once()
        # check that the sftpclient.retrieve method was called with the correct parameters
        mock_retrieve.assert_called_once_with(server_path="/instrument/WISH/RBNumber/RB87654321/4321/autoreduced/existing_file.png", local_path=None, override=True)

    @patch('utils.clients.sftp_client.SFTPClient.__init__', return_value=None)
    @patch('utils.clients.sftp_client.SFTPClient.get_filenames', return_value=[])
    @patch('utils.clients.sftp_client.SFTPClient.retrieve')
    def test_get_plot_file_WISH_None_plottype_no_file_found(self, mock_retrieve, mock_get_filenames, mock_client_init):
        """
        Test: PlotHandler.get_plot_file behaves correctly if no existing files have been found
        When: no plot file exists
        """
        # call the get_plot_file method and check it behaves correctly if no existing file is found (currently: return False)
        expected=False
        actual=self.test_WISH_None_plottype.get_plot_file()
        self.assertEqual(expected,actual)
        # check that the found file names are saved correctly
        self.assertEqual(self.test_WISH_None_plottype._existing_plot_files,[])
        # check number of times the sftpclient.get_filenames method was called
        expected=5
        actual=mock_get_filenames.call_count
        self.assertEqual(expected,actual)
        # check that the sftpclient.retrieve has not been called
        mock_retrieve.assert_not_called()

    def test_construct_plot(self):
        """
        Test:
        When:
        """
        pass
