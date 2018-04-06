"""
Designed to periodically check if the Data Archive for the most recent file.
This file is then compared to the reduction database to see if they are the same.
If not the run should be missing run should be restarted.
"""
import os
import glob
import logging
from EndOfRunMonitor.database_client import ReductionRun, Instrument

GENERIC_INST_PATH = r'\\isis\inst$\NDX{}\Instrument'


class ArchiveMonitor(object):
    """
    Check the data archive location and inspect
    the most recent run data for comparison to the reduction database
    """
    def __init__(self, instrument_name, database_session):
        """
        :param instrument_name: name of the instrument e.g. GEM, WISH
        :param database_session: An active database session to the MySQL
                                 reduction database
        """
        self.instrument = instrument_name
        self.instrument_path = GENERIC_INST_PATH.format(instrument_name)
        self.database_session = database_session

    def compare_most_recent_to_reduction_db(self):
        """
        Compare the most recent file from the data archive
        to the most recent data reduction entry
        :return: True - files match
                 False - files do not match
        """
        data_archive_file_name = self._get_most_recent_run_in_archive()
        run_no = ''.join([num for num in data_archive_file_name if num.isdigit()])

        last_run = self.database_session.query(ReductionRun).\
            filter_by(run_number=run_no).order_by('-run_version').first()

        if last_run == os.path.basename(data_archive_file_name):
            return True
        return False

    def get_most_recent_run_in_database(self, inst_name):
        """
        Get the most recent run in the reduction database
        (organised by time started) for an instrument
        :param inst_name: The name of the instrument to search for
        :return: The instrument name concatenated with the most recent run number
                 e.g. GEM1234
        """
        inst = self.database_session.query(Instrument).filter_by(name=inst_name).first()
        run = self.database_session.query(ReductionRun).filter_by(instrument_id=inst.id).order_by('started').first()
        return '%s%s' % (inst.name, run.run_number)

    def _get_most_recent_run_in_archive(self):
        """
        Flow control method to find current cycle directory and extract most recent file
        :return: returns the most recent file added to the directory
        """
        current_cycle = self._find_path_to_current_cycle_in_archive(os.path.join(self.instrument_path, 'logs'))
        return self._find_most_recent_run_in_archive(os.path.join(self.instrument_path, 'data', current_cycle))

    @staticmethod
    def _find_most_recent_run_in_archive(current_cycle_path):
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
        cycle_folders = [folder for folder in all_folders if folder.startswith('cycle')]

        # List should have most recent cycle at the end
        return cycle_folders[-1]
