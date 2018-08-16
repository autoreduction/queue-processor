# pylint:disable=anomalous-backslash-in-string
"""
Used to create a fake data-archive structure for testing

Usage example:

#  Creating an archive:
data_archive = DataArchiveCreator('C:\..\test\data-archive')
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
import os
import shutil
import time


GENERIC_CYCLE_PATH = os.path.join('NDX{}', 'Instrument', 'data', 'cycle_{}_{}')


class DataArchiveCreator(object):
    """
    Generates a data in the current working directory.
    The archive is designed to look identical to the
    implementation at ISIS
    """

    _base_dir = None

    _archive_dir_name = 'data-archive'
    _archive_dir = None

    _cycle_name = 'cycle_{}_{}'
    _end_year = None
    _end_iteration = None

    data_files = None
    archive_deleted = False

    def __init__(self, base_directory):
        """
        :param base_directory: user specified location to create the mock data archive
        """
        if os.path.isdir(base_directory):
            self._base_dir = base_directory
        else:
            raise RuntimeError('Unable to find base_directory %s. '
                               'Please ensure this directory exists' % base_directory)
        self.data_files = []
        self.archive_deleted = False
        self._create_archive_directory()

    def _create_archive_directory(self):
        """ Creates user/path/data-archive"""
        os.makedirs(os.path.join(self._base_dir, self._archive_dir_name))
        self._archive_dir = os.path.join(self._base_dir, self._archive_dir_name)

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
        instrument_dir_path = os.path.join(ndx_dir_path, 'Instrument')
        logs_dir_path = os.path.join(instrument_dir_path, 'logs')
        user_dir_path = os.path.join(ndx_dir_path, 'user')
        data_dir_path = os.path.join(instrument_dir_path, 'data')
        jrnl_dir_path = os.path.join(logs_dir_path, 'journal')
        for instrument in instruments:
            os.makedirs(user_dir_path.format(instrument))
            os.makedirs(data_dir_path.format(instrument))
            os.makedirs(jrnl_dir_path.format(instrument))
            self.make_cycle_directories(start_year, end_year, current_cycle,
                                        data_dir_path.format(instrument))

    def make_cycle_directories(self, start_year, end_year, current_cycle, base_dir):
        """
        Creates individual cycle directories from a given base directory
        :param start_year: The first year to create a dir for
        :param end_year: The final year to create a dir for
        :param current_cycle: The current cycle (1-5) in the final year
        :param base_dir: The directory to add the cycles to (normally instrument/data)
        """
        def create_single_years_cycles(end_iter, year):
            """
            Adds the cycles directories for a single year
            """
            if year < 10:
                year = '0{}'.format(year)
            for cycle_num in range(1, end_iter + 1):
                current_cycle_dir_name = self._cycle_name.format(year, cycle_num)
                os.makedirs(os.path.join(base_dir, current_cycle_dir_name))

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
        if cycle_year < 10:
            cycle_year = '0{}'.format(cycle_year)
        path_to_data_dir = os.path.join(self._archive_dir,
                                        GENERIC_CYCLE_PATH).format(instrument,
                                                                   cycle_year,
                                                                   cycle_iteration)
        for file_name in data_files:
            file_path = os.path.join(path_to_data_dir, file_name)
            self.create_file_at_location(file_path)

    def add_journal_file(self, instrument, file_contents):
        """
        Adds a journal (summary.txt) file to a given instruments directory
        :param instrument: The instrument to add the file to
        :param file_contents: the contents of the file (normally RB number)
        """
        path_to_log_file = os.path.join(self._archive_dir, 'NDX{}',
                                        'Instrument', 'logs',
                                        'journal').format(instrument)
        self.create_file_at_location(os.path.join(path_to_log_file, 'summary.txt'), file_contents)

    def add_last_run_file(self, instrument, file_contents):
        """
        Adds a lastrun.txt file to a given instruments directory
        :param instrument: The instrument to add the file to
        :param file_contents: the contents of the file (normally RB number)
        """
        path_to_log_file = os.path.join(self._archive_dir, 'NDX{}',
                                        'Instrument', 'logs').format(instrument)
        self.create_file_at_location(os.path.join(path_to_log_file, 'lastrun.txt'), file_contents)

    def create_file_at_location(self, file_path, contents=None):
        """
        Generic function to create a file at a given file_path with optional content
        :param file_path: The file path to create a file to
        :param contents: the optional content of the file
        """
        self.data_files.append(file_path)
        with open(file_path, 'w') as file_handle:
            if contents is not None:
                file_handle.write(contents)
        time.sleep(0.1)  # required as these files are order by modification date

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
        self.delete_all_files()
        shutil.rmtree(self._archive_dir)
        self.archive_deleted = True

    def __del__(self):
        """
        Ensure that the data archive is deleted on object deletion
        """
        if not self.archive_deleted:
            self.delete_archive()
