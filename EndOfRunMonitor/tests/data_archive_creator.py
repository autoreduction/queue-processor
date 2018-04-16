"""
Used to create a fake data-archive structure for testing
"""
import os
import shutil
import time


class DataArchiveCreator(object):

    _data_archive_dir_base = 'data-archive'
    _data_archive_dir = 'data-archive/{}/data/'
    _cycle_dir_name = 'cycle_{}_{}'
    _path_to_data_archive = ''
    _most_recent_cycle = None

    def __init__(self, instrument):
        self._data_archive_dir = self._data_archive_dir.format(instrument)
        self._path_to_data_archive = os.path.join(os.getcwd(), self._data_archive_dir)

    def get_data_archive_base(self):
        return self._data_archive_dir_base

    def get_data_archive_dir(self):
        return self._data_archive_dir

    def get_path_to_data_archive(self):
        return self._path_to_data_archive

    def get_most_recent_cycle_dir(self):
        return self._most_recent_cycle

    def get_path_to_most_recent_cycle(self):
        return os.path.join(self._path_to_data_archive, self._most_recent_cycle)

    def make_data_archive(self, start_year, end_year, current_cycle):
        """
        Creates a valid path structure (mirror of ISIS data archive)
        :param start_year: 1-2 digit start year e.g. 12 for 2012 (min 0 for 2000)
        :param end_year: 1-2 digit end year e.g. 14 for 2014 (max 99 for 2099)
        :param current_cycle: 1 digit [1-5]
        """
        data_archive_path = os.path.join(os.getcwd(), self._data_archive_dir)
        os.makedirs(data_archive_path)
        # Make all FULL cycle directories
        current_cycle_dir_name = ''
        for cycle_year in range(start_year, end_year):
            if cycle_year < 10:
                cycle_year = '0' + str(cycle_year)
            for cycle_num in range(1, 6):
                current_cycle_dir_name = self._cycle_dir_name.format(cycle_year, cycle_num)
                os.makedirs(os.path.join(data_archive_path, current_cycle_dir_name))

        # Make most current cycle directories (could by current cycle < 5
        if end_year < 10:
            end_year = '0' + str(end_year)
        for cycle_num in range(1, current_cycle+1):
            current_cycle_dir_name = self._cycle_dir_name.format(end_year, cycle_num)
            os.makedirs(os.path.join(data_archive_path, current_cycle_dir_name))
        self._most_recent_cycle = current_cycle_dir_name

    def add_files_to_most_recent_cycle(self, files_to_add):
        """
        Add a list of files to the most recent cycle
        :param files_to_add: list of the files to add
        """
        for file_name in files_to_add:
            file_path = os.path.join(self._data_archive_dir, self._most_recent_cycle, file_name)
            file_handle = open(file_path, 'w')
            file_handle.close()
            time.sleep(0.1)  # required as these files are order by modification date

    def remove_files_from_most_recent_cycle(self):
        """
        Removes all files from the most recent path. The directory will NOT be removed
        """
        path = os.path.join(self._data_archive_dir, self._most_recent_cycle)
        for files in os.listdir(path):
            os.remove(os.path.join(path, files))

    def remove_data_archive(self):
        shutil.rmtree(os.path.join(os.getcwd(), self._path_to_data_archive))

