"""
Unit tests and associated helpers to exercise the ISIS Archive Checker
"""
import unittest
import os
import shutil

from EndOfRunMonitor.ISIS_archive_monitor import ArchiveMonitor


class TestISISArchiveChecker(unittest.TestCase):
    """
    Contains test cases for the ArchiveMonitor
    """
    def test_init(self):
        monitor = ArchiveMonitor()
        self.assertIsInstance(monitor, ArchiveMonitor)


class TestArchiveMonitorHelpers(unittest.TestCase):
    """
    Contains test cases for ArchiveMonitor helper functions
    """
    def test_valid_find_path_to_current_cycle(self):
        _setup_valid_paths(0, 11, 3)

    #def tearDown(self):
        #shutil.rmtree(os.path.join(os.getcwd(), DATA_ARCHIVE_DIR))


# =========== Test helpers ============== #
DATA_ARCHIVE_DIR = 'data-archive'
CYCLE_DIR_NAME = 'cycle_{}_{}'


def _setup_valid_paths(start, end, current_cycle):
    """
    Creates a valid path structure (mirror of ISIS data archive)
    :param start: 1-2 digit start year e.g. 12 for 2012 (min 0 for 2000)
    :param end: 1-2 digit end year e.g. 14 for 2014 (max 99 for 2099)
    :param current_cycle: 1 digit [1-5]
    """
    data_archive_path = os.path.join(os.getcwd(), DATA_ARCHIVE_DIR)
    os.makedirs(data_archive_path)
    # Make all FULL cycle directories
    for cycle_year in range(start, end):
        if cycle_year < 10:
            cycle_year = '0' + str(cycle_year)
        for cycle_num in range(1, 6):
            cycle_dir_name = CYCLE_DIR_NAME.format(cycle_year, cycle_num)
            os.makedirs(os.path.join(data_archive_path, cycle_dir_name))

    # Make most current cycle directories (could by current cycle < 5
    if end < 10:
        end = '0' + str(end)
    for cycle_num in range(1, current_cycle+1):
        cycle_dir_name = CYCLE_DIR_NAME.format(end, current_cycle)
        os.makedirs(os.path.join(data_archive_path, cycle_dir_name))
