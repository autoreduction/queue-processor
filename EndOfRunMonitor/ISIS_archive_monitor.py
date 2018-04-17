"""
Designed to periodically check if the Data Archive for the most recent file.
This file is then compared to the reduction database to see if they are the same.
If not the run should be missing run should be restarted.
"""
import os
import logging

import ISIS_archive_monitor_helper as Helper
from EndOfRunMonitor.database_client import ReductionRun, Instrument

logging.basicConfig(filename=Helper.LOG_FILE, level=logging.DEBUG)


class ArchiveMonitor(object):
    """
    Check the data archive location and inspect
    the most recent run data for comparison to the reduction database
    """
    def __init__(self, instrument_name):
        """
        set the instrument param name and connect to the database
        :param instrument_name: name of the instrument e.g. GEM, WISH
        """
        instrument = instrument_name.upper()
        if instrument not in Helper.VALID_INST:
            logging.exception(Helper.INVALID_INSTRUMENT_MSG, instrument)
            raise RuntimeError(Helper.INVALID_INSTRUMENT_MSG, instrument)

        logging.info(Helper.START_UP_MSG, instrument)
        self.instrument = instrument
        self.instrument_path = Helper.GENERIC_INST_PATH.format(instrument)

        # Create the connection string for SQLAlchemy
        self.database_session = Helper.SESSION

    def get_most_recent_in_archive(self):
        """
        Flow control method to find current cycle directory and extract most recent file
        :return: returns the most recent file added to the directory
        """
        current_cycle = self._find_path_to_current_cycle_in_archive(os.path.join(self.instrument_path, 'data'))
        return self._find_most_recent_run_in_archive(os.path.join(self.instrument_path, 'data', current_cycle))

    def get_most_recent_run_in_database(self):
        """
        Get the most recent run in the reduction database
        (organised by time started) for an instrument
        :return: The instrument name concatenated with the most recent run number
                 e.g. GEM1234
        """
        # Find instrument
        inst = self.database_session.query(Instrument).filter_by(name=self.instrument).first()
        if inst is None:
            logging.warning(Helper.NO_INSTRUMENT_IN_DB_MSG, self.instrument)
            return None

        # Find run
        run = self.database_session.query(ReductionRun).filter_by(instrument_id=inst.id).order_by('started').first()
        if run is None:
            logging.warning(Helper.NO_RUN_FOR_INSTRUMENT_MSG, self.instrument)
            return None

        return '%s%s' % (inst.name, run.run_number)

    def compare_most_recent_to_reduction_db(self):
        """
        Compare the most recent file from the data archive
        to the most recent data reduction entry
        :return: True - files match
                 False - files do not match
        """
        data_archive_file_path = self.get_most_recent_in_archive()
        data_archive_file_name = os.path.splitext(data_archive_file_path)[0]

        last_database_run = self.get_most_recent_run_in_database()

        if last_database_run == data_archive_file_name:
            logging.info(Helper.RUN_MATCH_MSG, data_archive_file_name, last_database_run)
            return True
        logging.warning(Helper.RUN_MISMATCH_MSG, data_archive_file_name, last_database_run)
        return False

    @staticmethod
    def _find_most_recent_run_in_archive(current_cycle_path):
        """
        Given the most recent cycle path, find the most recent run
        :param current_cycle_path: full path to current cycle
        :return: The most recent file in the directory
        """
        base_dir = os.getcwd()
        os.chdir(current_cycle_path)
        # search all files in directory and return any that end in .raw or .RAW
        raw_files = [raw_file for raw_file in os.listdir(current_cycle_path)
                     if raw_file.endswith('.raw') or raw_file.endswith('.RAW')]

        # sort all files by modified time
        raw_files.sort(key=os.path.getmtime)
        os.chdir(base_dir)
        try:
            return raw_files[-1]
        except IndexError:
            logging.warning(Helper.NO_FILES_FOUND_MSG, current_cycle_path)
            return None

    @staticmethod
    def _find_path_to_current_cycle_in_archive(instrument_log_path):
        """
        Finds the most recent cycle (current) by inspection of the instrument folder
        Assumes that most recent cycle folder is the final folder in directory
        :param instrument_log_path: The path to the instrument folder given as -
                                    "\\isis\inst$\NDX%s\Instrument\log"
        :return: The most recent cycle folder
        """
        all_folders = os.listdir(instrument_log_path)
        cycle_folders = sorted([folder for folder in all_folders if folder.startswith('cycle')])

        # List should have most recent cycle at the end
        return cycle_folders[-1]
