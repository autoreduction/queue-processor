"""
Designed to periodically check if the Data Archive for the most recent file.
This file is then compared to the reduction database to see if they are the same.
If not the run should be missing run should be restarted.
"""
import os
import glob
import logging


class ArchiveMonitor(object):
    """
    Check the data archive location and inspect
    the most recent run data for comparison to the reduction database
    """
    def __init__(self, instrument_dir_path):
        self.instrument_path = instrument_dir_path

    def get_most_recent_run(self):
        """
        Flow control method to find current cycle directory and extract most recent file
        :return: returns the most recent file added to the directory
        """
        current_cycle = self._find_path_to_current_cycle(os.path.join(self.instrument_path, 'log'))
        return self._find_most_recent_run(os.path.join(self.instrument_path, 'data', current_cycle))

    @staticmethod
    def _find_path_to_current_cycle(instrument_log_path):
        """
        Finds the most recent cycle (current) by inspection of the instrument folder
        Assumes that most recent cycle folder is the final folder in directory
        :param instrument_log_path: The path to the instrument folder given as -
                                    "\\isis\inst$\NDX%s\Instrument\log"
        :return: The most recent cycle folder
        """
        all_folders = os.listdir(instrument_log_path)
        cycle_folders = [folder for folder in all_folders if folder.startswith('cycle')]

        # List should have most recent cycle at the end
        return cycle_folders[-1]

    @staticmethod
    def _find_most_recent_run(current_cycle_path):
        """
        Given the most recent cycle path, find the most recent run
        :param current_cycle_path: full path to current cycle
        :return: The most recent file in the directory
        """
        base_dir = os.getcwd()
        os.chdir(current_cycle_path)
        raw_files = [raw_file for raw_file in glob.glob("*.raw")]

        # sort all files by modified time
        raw_files.sort(key=os.path.getmtime)
        os.chdir(base_dir)
        try:
            return raw_files[-1]
        except IndexError:
            logging.warning("No files found when searching {}".format(current_cycle_path))
            return None
