"""
Unit tests and associated helpers to exercise the ISIS Archive Checker
"""
import unittest
import os
import shutil
import time

from EndOfRunMonitor.ISIS_archive_monitor import ArchiveMonitor

# List of variables to create a valid path and expected result _find_path_to_current_cycle
# [[start_year, end_year, current_cycle, expected_result], ...]
VALID_PATHS = [[0, 9, 3, 'cycle_09_3'],
               [1, 2, 5, 'cycle_02_5'],
               [10, 14, 1, 'cycle_14_1']]

# List of data to add to a directory and expected result from _find_most_recent_run
FILES_TO_TEST = [['TEST01.raw', 'TEST02.raw', 'TEST03.raw', 'TEST03.raw'],  # .raw
                 ['TEST01.RAW', 'TEST02.RAW', 'TEST03.RAW', 'TEST03.RAW'],  # .RAW
                 ['TEST01.raw', 'TEST02.RAW', 'TEST03.raw', 'TEST03.raw'],  # .raw/.RAW
                 ['TEST01.raw', 'TEST03.raw', 'TEST03.log', 'TEST03.raw'],  # .log file
                 ['TEST01.txt', 'TEST02.log', 'TEST01.out', None],  # no .raw
                 [None]]  # Empty file


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
        for item in VALID_PATHS:
            _setup_valid_paths(item[0], item[1], item[2])
            actual = ArchiveMonitor._find_path_to_current_cycle(DATA_ARCHIVE_DIR)
            self.assertEqual(item[3], actual)
            shutil.rmtree(os.path.join(os.getcwd(), DATA_ARCHIVE_DIR))

    def test_valid_find_most_recent_run(self):
        _setup_valid_paths(VALID_PATHS[2][0], VALID_PATHS[2][1], VALID_PATHS[2][2])
        path_to_cycle = os.path.join(os.getcwd(), DATA_ARCHIVE_DIR, VALID_PATHS[2][3])
        for test_files in FILES_TO_TEST:
            _add_files_to_path(path_to_cycle, test_files[:-1])
            actual = ArchiveMonitor._find_most_recent_run(path_to_cycle)
            self.assertEqual(test_files[-1], actual)
            _remove_files_from_path(path_to_cycle)
        shutil.rmtree(os.path.join(os.getcwd(), DATA_ARCHIVE_DIR))


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
        cycle_dir_name = CYCLE_DIR_NAME.format(end, cycle_num)
        os.makedirs(os.path.join(data_archive_path, cycle_dir_name))


def _add_files_to_path(path, files_to_add):
    """
    Add a list of files to a specific path
    :param path: path to add the files to
    :param files_to_add: list of the files to add
    """
    for file_name in files_to_add:
        file_path = os.path.join(path, file_name)
        file_handle = open(file_path, 'w')
        file_handle.close()


def _remove_files_from_path(path):
    """
    Removes all files from a given path. The directory will NOT be removed
    :param path: path to remove files from
    """
    for files in os.listdir(path):
        os.remove(os.path.join(path, files))