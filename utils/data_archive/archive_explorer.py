"""
Functionality designed to allow for easy data extraction from the isis archive
"""
import os

from utils.data_archive.file_filter import filter_files_by_time, filter_files_by_extension


class ArchiveExplorer(object):
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
        return self._file_path_exists((os.path.join(self._archive_base_directory,
                                                    'NDX{}').format(instrument)))

    def get_instrument_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument """
        return self._file_path_exists(os.path.join(self.get_ndx_directory(instrument),
                                                   'Instrument'))

    def get_user_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/user """
        return self._file_path_exists(os.path.join(self.get_ndx_directory(instrument),
                                                   'user'))

    # ================================= Log directories ========================================= #
    def get_log_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/logs """
        return self._file_path_exists(os.path.join(self.get_instrument_directory(instrument),
                                                   'logs'))

    def get_journal_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/logs/journal """
        return self._file_path_exists(os.path.join(self.get_log_directory(instrument),
                                                   'journal'))

    def get_last_run_file(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/logs/lastrun.txt """
        return self._file_path_exists(os.path.join(self.get_log_directory(instrument),
                                                   'lastrun.txt'))

    def get_summary_file(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/logs/journal/summary.txt """
        return self._file_path_exists(os.path.join(self.get_journal_directory(instrument),
                                                   'summary.txt'))

    # ================================== Data directories ======================================= #
    def get_data_directory(self, instrument):
        """ :return: archive_directory/NDXGEM/Instrument/data """
        return self._file_path_exists(os.path.join(self.get_instrument_directory(instrument),
                                                   'data'))

    def get_cycle_directory(self, instrument, year, cycle_number):
        """
        Attempt to find a cycle from input
        :return: archive_directory/NDXGEM/Instrument/data/cycle_<year>_<cycle_number>
        """
        return self._file_path_exists(os.path.join(self.get_data_directory(instrument),
                                                   "cycle_{}_{}").format(year, cycle_number))

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
        time_filtered_files = filter_files_by_time(self.get_current_cycle_directory(instrument),
                                                   cut_off_time)
        valid_files = filter_files_by_extension(time_filtered_files, ('.nxs', '.raw'))
        valid_files.sort(key=os.path.getmtime)
        if valid_files:
            return valid_files[-1]
        return None

    def get_rb_for_run_num(self, instrument, run_number, limit):
        """
        Find the RB number for a given run number
        :param instrument: The instrument associated with the run
        :param run_number: The run number to search for
        :param limit: numbers are read from the last data entry up,
                      the limit is how far we should look up the list
        :return: The RB number associated with the run number
        """
        with open(self.get_summary_file(instrument), 'r') as summary_file:
            data = summary_file.readlines()[-limit:]
        for line in data:
            if "{}{}".format(instrument.upper(), run_number) in line:
                rb_number = line.split(" ")[-1].strip()
                if int(rb_number) > 0:  # Ensure not a calibration run we are checking against
                    return rb_number
        return False
