# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test the archive explorer
"""
import datetime
import os
import shutil
import tempfile
import unittest

from utils.data_archive.data_archive_creator import DataArchiveCreator
from utils.data_archive.archive_explorer import ArchiveExplorer


# pylint:disable=invalid-name,too-many-public-methods
class TestArchiveExplorer(unittest.TestCase):
    """
    Test all the functionality of the archive explorer
    """

    test_output_directory = None

    @classmethod
    def setUpClass(cls):
        """
        Create the test output directory and the data archive directory
        """
        cls.test_output_directory = tempfile.mkdtemp()
        cls.archive_directory = os.path.join(cls.test_output_directory, 'data-archive')

    def setUp(self):
        """
        Initialise the DataArchiveCreator object and create cycle directories
        """
        self.dac = DataArchiveCreator(self.test_output_directory)
        self.dac.make_data_archive(['GEM', 'WISH', 'MUSR'], 17, 18, 2)
        self.explorer = ArchiveExplorer(self.archive_directory)

    def test_ndx_path(self):
        """ Test path to NDX directory """
        expected = os.path.join(self.archive_directory, 'NDXGEM')
        actual = self.explorer.get_ndx_directory('GEM')
        self.assertEqual(actual, expected)

    def test_instrument_path(self):
        """ Test path to instrument directory """
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument')
        actual = self.explorer.get_instrument_directory('GEM')
        self.assertEqual(actual, expected)

    def test_user_path(self):
        """ Test path to user directory """
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'user')
        actual = self.explorer.get_user_directory('GEM')
        self.assertEqual(actual, expected)

    def test_log_path(self):
        """ Test path to logs directory """
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument', 'logs')
        actual = self.explorer.get_log_directory('GEM')
        self.assertEqual(actual, expected)

    def test_journal_path(self):
        """ Test path to journal directory """
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument', 'logs', 'journal')
        actual = self.explorer.get_journal_directory('GEM')
        self.assertEqual(actual, expected)

    def test_last_run_file_path(self):
        """ Test path to lastrun.txt file """
        self.dac.add_last_run_file('GEM', 'test')
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument', 'logs', 'lastrun.txt')
        actual = self.explorer.get_last_run_file('GEM')
        self.assertEqual(actual, expected)

    def test_summary_file_path(self):
        """ Test path to summary.txt file """
        self.dac.add_journal_file('GEM', 'test')
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument', 'logs', 'journal', 'summary.txt')
        actual = self.explorer.get_summary_file('GEM')
        self.assertEqual(actual, expected)

    def test_reduce_file_path(self):
        """ Test path to reduce.py file """
        self.dac.add_reduce_script('GEM', 'test')
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'user', 'scripts', 'autoreduction', 'reduce.py')
        actual = self.explorer.get_reduce_file('GEM')
        self.assertEqual(actual, expected)

    def test_reduce_vars_file_path(self):
        """ Test path to reduce_vars.py file """
        self.dac.add_reduce_vars_script('GEM', 'test')
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'user', 'scripts', 'autoreduction', 'reduce_vars.py')
        actual = self.explorer.get_reduce_vars_file('GEM')
        self.assertEqual(actual, expected)

    def test_data_dir_path(self):
        """ Test path to data directory """
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument', 'data')
        actual = self.explorer.get_data_directory('GEM')
        self.assertEqual(actual, expected)

    def test_custom_cycle_dir_path(self):
        """ Test path to custom defined cycle directory """
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument', 'data', 'cycle_17_2')
        actual = self.explorer.get_cycle_directory('GEM', 17, 2)
        self.assertEqual(actual, expected)

    def test_custom_cycle_dir_does_not_exist(self):
        """ Test exception raised if custom cycle doesn't exist """
        self.assertRaises(OSError, self.explorer.get_cycle_directory, "GEM", 10, 1)

    def test_current_cycle_dir_path(self):
        """ Test path to most recent cycle directory """
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument', 'data', 'cycle_18_2')
        actual = self.explorer.get_current_cycle_directory('GEM')
        self.assertEqual(actual, expected)

    def test_current_cycle_directory_not_exist(self):
        """ Test current cycle returns None when directory is empty """
        self.dac.delete_archive()
        os.makedirs(os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'data'))
        self.assertIsNone(self.explorer.get_current_cycle_directory('GEM'))
        shutil.rmtree(os.path.join(self.test_output_directory, 'data-archive'))

    def test_get_most_recent_run_empty(self):
        """ Test path to most recent run if none exist """
        self.assertIsNone(self.explorer.get_most_recent_run_since('GEM', datetime.datetime.now()))

    def test_get_most_recent_run_add_before_cut_off(self):
        """ Test path to most recent run if only run before time cut off exist """
        self.dac.add_data_to_most_recent_cycle('GEM', ['GEM001.nxs'])
        test_start_time = datetime.datetime.now()
        actual = self.explorer.get_most_recent_run_since('GEM', test_start_time)
        self.assertIsNone(actual)

    def test_get_most_recent_run_single(self):
        """ Test path valid most recent run """
        expected = os.path.join(self.archive_directory, 'NDXGEM', 'Instrument', 'data', 'cycle_18_2', 'GEM001.nxs')
        # Ensure that the time is set in the past - Note we can not rely on the system clock for
        # this as the linux system clock does not always match up with file modification times
        time_in_past = datetime.datetime.fromtimestamp(10000)
        self.dac.add_data_to_most_recent_cycle('GEM', ['GEM001.nxs'])
        actual = self.explorer.get_most_recent_run_since('GEM', time_in_past)
        self.assertEqual(actual, expected)

    def tearDown(self):
        """
        Delete the data archive - this will also clean up any files left behind
        """
        del self.dac

    @classmethod
    def tearDownClass(cls):
        """
        Remove the test data directory
        """
        shutil.rmtree(cls.test_output_directory)
