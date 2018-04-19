"""
Used to create a fake data-archive structure for testing
"""
import os
import shutil
import time


class DataArchiveCreator(object):
    """
    Generates a data in the current working directory.
    The archive is designed to look identical to the
    implementation at ISIS
    """

    _base_dir = None
    _instrument = None

    _archive_dir_name = 'data-archive'
    archive_dir = None

    _data_archive_dir_name = '{}/data/'
    data_archive_dir = None

    _cycle_name = 'cycle_{}_{}'
    _most_recent_cycle_dir = None

    def __init__(self, instrument, base_directory):
        """
        :param instrument: The instrument to create the directory for e.g. WISH
        :param base_directory: user specified location to create the mock data archive
        """
        self._instrument = instrument
        if os.path.isdir(base_directory):
            self._base_dir = base_directory
        else:
            raise RuntimeError('Unable to find base_directory %S.'
                               'Please ensure this directory exists', base_directory)
        self._create_archive_directory()
        self._create_data_archive_directory()

    def get_most_recent_cycle_dir(self):
        """
        Returns the most recent cycle directory if not None
        :return: The most recent cycle directory or
                 raise exception is not set
        """
        if self._most_recent_cycle_dir:
            return self._most_recent_cycle_dir
        else:
            raise RuntimeError('The most recent cycle directory is currently \'None\'.'
                               'Please ensure you have run make_data_archive')

    def _create_archive_directory(self):
        """ Creates user/path/data-archive"""
        os.makedirs(os.path.join(self._base_dir, self._archive_dir_name))
        self.archive_dir = os.path.join(self._base_dir, self._archive_dir_name)

    def _create_data_archive_directory(self):
        """ Creates user/path/data-archive/{inst}/data"""
        os.makedirs(os.path.join(self.archive_dir,
                                 self._data_archive_dir_name.format(self._instrument)))
        self.data_archive_dir = os.path.join(self.archive_dir,
                                             self._data_archive_dir_name.format(self._instrument))

    def make_data_archive(self, start_year, end_year, current_cycle):
        """
        Creates a valid path structure (mirror of ISIS data archive)
        :param start_year: 1-2 digit start year e.g. 12 for 2012 (min 0 for 2000)
        :param end_year: 1-2 digit end year e.g. 14 for 2014 (max 99 for 2099)
        :param current_cycle: 1 digit [1-5]
        """
        # Make all FULL cycle directories
        current_cycle_dir_name = ''
        for cycle_year in range(start_year, end_year):
            if cycle_year < 10:
                cycle_year = '0' + str(cycle_year)
            for cycle_num in range(1, 6):
                current_cycle_dir_name = self._cycle_name.format(cycle_year, cycle_num)
                os.makedirs(os.path.join(self.data_archive_dir, current_cycle_dir_name))

        # Make most current cycle directories (could by current cycle < 5
        if end_year < 10:
            end_year = '0' + str(end_year)
        for cycle_num in range(1, current_cycle+1):
            current_cycle_dir_name = self._cycle_name.format(end_year, cycle_num)
            os.makedirs(os.path.join(self.data_archive_dir, current_cycle_dir_name))
        self._most_recent_cycle_dir = os.path.join(self.data_archive_dir, current_cycle_dir_name)

    def add_most_recent_cycle_files(self, files_to_add):
        """
        Add a list of files to the most recent cycle
        :param files_to_add: list of the files to add
        """
        for file_name in files_to_add:
            file_path = os.path.join(self.data_archive_dir, self._most_recent_cycle_dir, file_name)
            with open(file_path, 'w') as _:
                pass
            time.sleep(0.1)  # required as these files are order by modification date

    def remove_most_recent_cycle_files(self):
        """
        Removes all files from the most recent path.
        The directory will NOT be removed
        """
        path = os.path.join(self.data_archive_dir,
                            self._most_recent_cycle_dir)
        if os.path.isdir(path):
            all_files = os.listdir(path)
            for files in all_files:
                os.remove(os.path.join(path, files))

    def remove_data_archive(self):
        """
        Remove data archive from system
        """
        shutil.rmtree(self.archive_dir)

    def __del__(self):
        """Ensure that the data archive is deleted on object deletion"""
        try:
            self.remove_data_archive()
        except OSError:
            # Some tests will delete the output as part of the test
            pass
