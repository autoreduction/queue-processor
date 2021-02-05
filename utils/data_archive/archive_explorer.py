# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Functionality designed to allow for easy data extraction from the isis archive
"""
import os

from utils.data_archive.file_filter import filter_files_by_time, filter_files_by_extension


class ArchiveExplorer:
    """
    Various functions for extracting data from different commonly
    accessed locations in the data archive
    """

    _archive_base_directory = None

    def __init__(self, archive_directory):
        self._archive_base_directory = archive_directory

    @staticmethod
    def _file_path_exists(file_path):
        if os.path.exists(file_path):
            return file_path
        raise OSError("File path: {} does not exist.".format(file_path))

    def get_ndx_directory(self, instrument):
        """ :return: archive_directory/NDXGEM """
        return self._file_path_exists((os.path.join(self._archive_base_directory, 'NDX{}').format(instrument)))

    def get_instrument_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument """
        return self._file_path_exists(os.path.join(self.get_ndx_directory(instrument), 'Instrument'))

    def get_user_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/user """
        return self._file_path_exists(os.path.join(self.get_ndx_directory(instrument), 'user'))

    # ================================= Log directories ========================================= #
    def get_log_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/logs """
        return self._file_path_exists(os.path.join(self.get_instrument_directory(instrument), 'logs'))

    def get_journal_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/logs/journal """
        return self._file_path_exists(os.path.join(self.get_log_directory(instrument), 'journal'))

    def get_last_run_file(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/logs/lastrun.txt """
        return self._file_path_exists(os.path.join(self.get_log_directory(instrument), 'lastrun.txt'))

    def get_summary_file(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/logs/journal/summary.txt """
        return self._file_path_exists(os.path.join(self.get_journal_directory(instrument), 'summary.txt'))

    # ================================== Data directories ======================================= #
    def get_data_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/data """
        return self._file_path_exists(os.path.join(self.get_instrument_directory(instrument), 'data'))

    def get_cycle_directory(self, instrument, year, cycle_number):
        """
        Attempt to find a cycle from input
        :return: archive_directory/NDXGEM/Instrument/data/cycle_<year>_<cycle_number>
        """
        return self._file_path_exists(
            os.path.join(self.get_data_directory(instrument), "cycle_{}_{}").format(year, cycle_number))

    def get_current_cycle_directory(self, instrument):
        """
        Return the most recent cycle directory for an instrument
        :return: archive_directory/NDXGEM/Instrument/data/cycle_18_1
        """
        data_directory = self.get_data_directory(instrument)
        all_folders = os.listdir(data_directory)
        cycle_folders = sorted([folder for folder in all_folders if folder.startswith('cycle')])

        # List should have most recent cycle at the end
        if cycle_folders:
            return os.path.join(data_directory, cycle_folders[-1])
        return None

    def get_most_recent_run_since(self, instrument, cut_off_time):
        """
        Return the latest run in the archive for the instrument after a given time
        :param instrument: The instrument associated with the desired run
        :param cut_off_time: Time to filter files by
        :return: archive_directory/NDXGEM/Instrument/data/cycle_18_1/GEM001.nxs
        """
        time_filtered_files = filter_files_by_time(self.get_current_cycle_directory(instrument), cut_off_time)
        valid_files = filter_files_by_extension(time_filtered_files, ('.nxs', '.raw'))
        valid_files.sort(key=os.path.getmtime)
        if valid_files:
            return valid_files[-1]
        return None

    # ============================= Script Directories ===================================== #
    def get_script_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/user/scripts/autoreduce"""
        return self._file_path_exists(os.path.join(self.get_user_directory(instrument), 'scripts', 'autoreduction'))

    def get_reduce_file(self, instrument):
        """ :return: archive_directory/NDXGEM/user/scripts/autoreduce/reduce.py"""
        return self._file_path_exists(
            os.path.join(self.get_script_directory(instrument), 'reduce.py').format(instrument))

    def get_reduce_vars_file(self, instrument):
        """ :return: archive_directory/NDXGEM/user/scripts/autoreduce/reduce.py"""
        return self._file_path_exists(os.path.join(self.get_script_directory(instrument), 'reduce_vars.py'))
