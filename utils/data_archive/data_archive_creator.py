# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint:disable=anomalous-backslash-in-string
"""
Used to create a fake data-archive structure for testing

Usage example:

#  Creating an archive:
data_archive = DataArchiveCreator('/../test/data-archive')
data_archive.make_data_archive(['GEM', 'POLARIS'], start_year=5, end_year=18, current_cycle=1)


#  Add file to the data directory:
data_archive.add_data_files_to_most_recent_cycle('GEM', ['something.txt'])
data_archive.add_data_files('GEM', 18, 1, 'something.txt') # This does the same as the above


#  Add file to the journal directory (used to find RB numbers)
data_archive.add_journal_file('GEM', 'file_contents 002 2201')


#  Access files and directories
data_archive.get_most_recent_cycle_for_instrument('GEM')
data_archive.get_journal_dir_for_instrument('GEM')
data_archive.get_data_most_recent_dir_for_instrument('GEM')


#  Deleting the directory
data_archive.delete_all_files()    # remove all files (not folders)
data_archive.delete_archive()      # remove all files and folders

"""
import calendar
import os
import shutil
import time
from utils.settings import VALID_INSTRUMENTS

GENERIC_CYCLE_PATH = os.path.join('NDX{}', 'Instrument', 'data', 'cycle_{}_{}')


class DataArchiveCreator:
    """
    Generates a data in the current working directory.
    The archive is designed to look identical to the
    implementation at ISIS
    """

    _base_dir = ''

    _archive_dir_name = 'data-archive'
    _archive_dir = None

    _cycle_name = 'cycle_{}_{}'
    _end_year = None
    _end_iteration = None

    data_files = []
    archive_deleted = False

    def __init__(self, base_directory, overwrite=False):
        """
        :param base_directory: user specified location to create the mock data archive
        :param overwrite: If True, this will overwrite the Archive in the base_directory
        """
        self.data_files = []
        self.archive_deleted = False
        if os.path.isdir(base_directory):
            self._base_dir = base_directory
        else:
            raise RuntimeError('Unable to find base_directory %s. '
                               'Please ensure this directory exists' % base_directory)
        # Delete the data-archive directory if it already exists
        if overwrite:
            if os.path.exists(os.path.join(base_directory, self._archive_dir_name)):
                shutil.rmtree(os.path.join(base_directory, self._archive_dir_name))
        self._create_archive_directory()

    def _create_archive_directory(self):
        """ Creates user/path/data-archive"""
        os.makedirs(os.path.join(self._base_dir, self._archive_dir_name))
        self._archive_dir = os.path.join(self._base_dir, self._archive_dir_name)
        self.archive_deleted = False

    def make_data_archive(self, instruments, start_year, end_year, current_cycle):
        """
        Create a full multi-instrument directory structure to mirror the ISIS data archive
        :param instruments: A list of all valid instruments to create directories for
        :param start_year: The first year to create a dir for
        :param end_year: The final year to create a dir for
        :param current_cycle: The current cycle (1-5) in the final year
        """
        self._end_year = end_year
        self._end_iteration = current_cycle
        ndx_dir_path = os.path.join(self._archive_dir, 'NDX{}')
        inst_dir_path = os.path.join(ndx_dir_path, 'Instrument')
        logs_dir_path = os.path.join(inst_dir_path, 'logs')
        user_dir_path = os.path.join(ndx_dir_path, 'user')
        data_dir_path = os.path.join(inst_dir_path, 'data')
        jrnl_dir_path = os.path.join(logs_dir_path, 'journal')
        scrp_dir_path = os.path.join(user_dir_path, 'scripts')
        auto_dir_path = os.path.join(scrp_dir_path, 'autoreduction')
        for instrument in instruments:
            os.makedirs(user_dir_path.format(instrument))
            os.makedirs(data_dir_path.format(instrument))
            os.makedirs(jrnl_dir_path.format(instrument))
            os.makedirs(auto_dir_path.format(instrument))
            self._make_cycle_directories(start_year, end_year, current_cycle, inst_dir_path.format(instrument))

    def _make_cycle_directories(self, start_year, end_year, current_cycle, base_dir):
        """
        Creates individual cycle directories to the data and log directory of the given
        base directory
        :param start_year: The first year to create a dir for
        :param end_year: The final year to create a dir for
        :param current_cycle: The current cycle (1-5) in the final year
        :param base_dir: the instrument directory
        """
        def create_single_years_cycles(end_iter, year):
            """
            Adds the cycles directories for a single year
            """
            if year < 10:
                year = '0{}'.format(year)
            for cycle_num in range(1, end_iter + 1):
                current_cycle_dir_name = self._cycle_name.format(year, cycle_num)
                os.makedirs(os.path.join(base_dir, 'data', current_cycle_dir_name))
                os.makedirs(os.path.join(base_dir, 'logs', current_cycle_dir_name))

        # Make all FULL cycle directories
        for cycle_year in range(start_year, end_year):
            create_single_years_cycles(5, cycle_year)

        # Make most current cycle directories (could by current cycle < 5)
        create_single_years_cycles(current_cycle, end_year)

    def add_data_to_most_recent_cycle(self, instrument, data_files):
        """
        Adds data files to the most recent cycle for that instrument
        :param instrument: The instrument to add the files for
        :param data_files: The files to add
        """
        self.add_data_files(instrument, self._end_year, self._end_iteration, data_files)

    def add_data_files(self, instrument, cycle_year, cycle_iteration, data_files):
        """
        Add a data file to a particular instrument directory
        :param instrument: The instrument the file relates to
        :param cycle_year: The cycle year for the file to be added to
        :param cycle_iteration: The cycle iteration for the file to be added to
        :param data_files: The data file name
        """
        if isinstance(data_files, str):
            data_files = [data_files]
        elif not isinstance(data_files, list):
            raise TypeError("data_files is of: {}. " "Valid type are list or str".format(type(data_files)))

        if cycle_year < 10:
            cycle_year = '0{}'.format(cycle_year)
        path_to_data_dir = os.path.join(self._archive_dir,
                                        GENERIC_CYCLE_PATH).format(instrument, cycle_year, cycle_iteration)
        for file_name in data_files:
            file_path = os.path.join(path_to_data_dir, file_name)
            self.create_file_at_location(file_path)

    def add_journal_file(self, instrument, file_contents):
        """
        Adds a journal (summary.txt) file to a given instruments directory
        :param instrument: The instrument to add the file to
        :param file_contents: the contents of the file (normally RB number)
        """
        path_to_log_file = os.path.join(self._archive_dir, 'NDX{}', 'Instrument', 'logs', 'journal',
                                        'summary.txt').format(instrument)
        self.create_file_at_location(path_to_log_file, str(file_contents))

    def add_reduce_script(self, instrument, file_content):
        """
        Adds the reduce.py file to the /user/scripts/autoreduce directory
        :param instrument: The instrument to add the file for
        :param file_content: The content of the file
        """
        path_to_reduce_file = os.path.join(self._archive_dir, 'NDX{}', 'user', 'scripts', 'autoreduction',
                                           'reduce.py').format(instrument)
        self.create_file_at_location(path_to_reduce_file, file_content)

    def add_reduce_vars_script(self, instrument, file_content):
        """
        Adds the reduce.py file to the /user/scripts/autoreduce directory
        :param instrument: The instrument to add the file for
        :param file_content: The content of the file
        """
        path_to_reduce_file = os.path.join(self._archive_dir, 'NDX{}', 'user', 'scripts', 'autoreduction',
                                           'reduce_vars.py').format(instrument)
        self.create_file_at_location(path_to_reduce_file, file_content)

    def add_last_run_file(self, instrument, file_contents):
        """
        Adds a lastrun.txt file to a given instruments directory
        :param instrument: The instrument to add the file to
        :param file_contents: the contents of the file (normally RB number)
        """
        path_to_log_file = os.path.join(self._archive_dir, 'NDX{}', 'Instrument', 'logs').format(instrument)
        self.create_file_at_location(os.path.join(path_to_log_file, 'lastrun.txt'), file_contents)

    def create_file_at_location(self, file_path, contents=None):
        """
        Generic function to create a file at a given file_path with optional content
        :param file_path: The file path to create a file to
        :param contents: the optional content of the file
        """
        try:
            creation_time = calendar.timegm(time.gmtime())
            with open(file_path, 'w') as file_handle:
                if contents is not None:
                    file_handle.write(contents)
            os.utime(file_path, (creation_time, creation_time))
            self.data_files.append(file_path)
        except IOError as exp:
            raise RuntimeError("Unable to create file at desired location. "
                               "Make sure this directory has been created "
                               "in the archive.\n    "
                               "Invalid file path: {}".format(file_path)) from exp

    def overwrite_file_content(self, file_path, new_file_contents):
        """
        Overwrite data in a file
        This can only be used for files that already exist and are present in self.data_files
        :param file_path: Path to the file you wish to overwrite
        :param new_file_contents: The new content for the file
        """
        if not os.path.exists(file_path) or file_path not in self.data_files:
            raise ValueError("File path: {} \n" "Either does not exist or is not present in self.data_files")

        with open(file_path, 'w') as file_handle:
            file_handle.write(new_file_contents)

    def delete_file(self, file_path):
        """
        Delete a file and remove it from the self.data_files
        :param file_path: the file path to the file to delete
        """
        if not os.path.exists(file_path) or file_path not in self.data_files:
            raise ValueError("File path: {} \n" "Either does not exist or is not present in self.data_files")
        os.remove(file_path)
        self.data_files.remove(file_path)

    def delete_all_files(self):
        """
        Removes all files in the data archive
        """
        if self.data_files:
            for file_path in self.data_files:
                os.remove(file_path)
            self.data_files = []

    def delete_archive(self):
        """
        Removes the full data archive
        """
        if not self.archive_deleted:
            self.delete_all_files()
            if self._archive_dir:
                shutil.rmtree(self._archive_dir)
            self.archive_deleted = True

    def __del__(self):
        """
        Ensure that the data archive is deleted on object deletion
        """
        if not self.archive_deleted:
            self.delete_archive()
