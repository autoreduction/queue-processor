# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import unittest
from plotting.plot_handler import PlotHandler

test_run_number=12345
test_instrument_name=MARI
test_rb_number=12345678

class TestPlotHandler(unittest.TestCase):
    """
    Test all the functionality of the PlotHandler
    """

    def setUp(self):
        """
        Create the test PlotHandler object
        """
        self.plothandler=PlotHandler(instrument_name="MARI",rb_number=12345678, run_number=1234, plot_type="png")

    def test_init(self):
        self.assertEqual(self.plothandler.instrument_name,"MARI")
        self.assertEqual(self.plothandler.rb_number, 12345678)
        self.assertEqual(self.plothandler.run_number, 1234)
        self.assertEqual(self.plothandler.plot_type, ["png"])
        self.assertEqual(self.plothandler._RBfolder, "/instrument/MARI/RBNumber/RB12345678/1234/autorecuced/")
        self.assertIsNone(self.plothandler.plot_file_path)

    def test_get_single_plot_file(self):
        """
        Call the SFTP client to get a single plot file from CEPH.
        """
        pass

    def test_get_plot_file(self):
        """
        Searches for and retrieves a plot file from CEPH. Can search for multiple plot files
        """
        pass

    def test_regexp_for_file_name(self):
        """
        Regular expression used for looking up plot files.
        """
        expected="MAR[I]12345*.png"
        actual=self.plothandler._regexp_for_file_name(self.plothandler.run_number, self.plothandler.plot_type)
        self.assertEqual(actual,expected)

    def test_construct_plot(self):
        """
        Calls the plot factory to construct an iframe.
        """
