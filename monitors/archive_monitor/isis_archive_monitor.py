"""
Designed to periodically check if the Data Archive for the most recent file.
This file is then compared to the reduction database to see if they are the same.
If not the run should be missing run should be restarted.
"""
import datetime
import json
import logging
import os

import monitors.archive_monitor.isis_archive_monitor_helper as helper
from utils.settings import ARCHIVE_MONITOR_LOG, INST_PATH
from utils.clients.database_client import DatabaseClient
from utils.clients.queue_client import QueueClient

logging.basicConfig(filename=ARCHIVE_MONITOR_LOG, level=logging.DEBUG,
                    format=helper.LOG_FORMAT)


class ArchiveMonitor(object):
    """
    Check the data archive location and inspect
    the most recent run data for comparison to the reduction database
    """

    _time_of_last_check = None

    def __init__(self, instrument_name=None):
        """
        set the instrument param name and connect to the database
        :param instrument_name: name of the instrument e.g. GEM, WISH
                                if None, assumed to be checking all known instruments
                                via perform check
        """
        instrument = instrument_name.upper()
        if instrument not in helper.VALID_INST and instrument is not None:
            logging.error(helper.INVALID_INSTRUMENT_MSG, instrument)
            raise RuntimeError(helper.INVALID_INSTRUMENT_MSG, instrument)

        self.instrument = instrument
        self.instrument_path = INST_PATH.format(instrument)
        self._update_check_time()

        # Create the sessions
        self._database_client = DatabaseClient()
        self.database_session = self._database_client.get_connection()
        logging.getLogger("stomp.py").setLevel(logging.WARNING)
        self.queue_session = QueueClient().get_connection()

    def perform_check(self):
        """
        Polls all the valid instruments
        """
        # Poll all valid instruments
        logging.info(helper.STATUS_OF_CHECKS_MSG, 'starting', self._time_of_last_check)
        for instrument in helper.VALID_INST:
            self.instrument = instrument
            self.instrument_path = INST_PATH.format(instrument)
            if not os.path.isdir(self.instrument_path):
                raise RuntimeError("Unable to find instrument directory at path %s. "
                                   "Please ensure the path is valid and then restart the service."
                                   % self.instrument_path)
            logging.info(helper.CHECKING_INST_MSG, instrument)
            self.compare_archive_to_database()
        logging.info(helper.STATUS_OF_CHECKS_MSG, 'complete', self._time_of_last_check)
        logging.info(helper.SLEEP_MSG)
        self._update_check_time()

    def _update_check_time(self):
        """
        Updates the timer that stores when the last check was made
        """
        self._time_of_last_check = datetime.datetime.now()

    def get_most_recent_in_archive(self):
        """
        Flow control method to find current cycle directory and extract most recent file
        :return: returns the most recent file added to the directory
        """
        data_archive_path = os.path.join(self.instrument_path, 'data')
        current_cycle = self._find_path_to_current_cycle_in_archive(data_archive_path)

        current_cycle_path = os.path.join(data_archive_path, current_cycle)
        return self._find_most_recent_run_in_archive(current_cycle_path)

    # pylint:disable=inconsistent-return-statements
    def get_most_recent_run_in_database(self):
        """
        Get the most recent run in the reduction database
        (organised by time started) for an instrument
        :return: The instrument name concatenated with the most recent run number
                 e.g. GEM1234
        """
        # Find instrument
        instrument_model = self._database_client.instrument()
        inst = self.database_session.query(instrument_model).filter_by(name=self.instrument).first()
        if inst is None:
            logging.warning(helper.NO_INSTRUMENT_IN_DB_MSG, self.instrument)
            return None

        # Find run ordered by most recently started
        reduction_model = self._database_client.reduction_run()
        run = self.database_session.query(reduction_model).\
            filter_by(instrument_id=inst.id).order_by('started').first()
        if run is None:
            logging.warning(helper.NO_RUN_FOR_INSTRUMENT_MSG, self.instrument)
            return None

        return '%s%s' % (inst.name, run.run_number)

    def compare_archive_to_database(self):
        """
        Compare the most recent file from the data archive
        to the most recent data reduction entry
        :return: True - files match
                 False - files do not match
        """
        data_archive_file_path = self.get_most_recent_in_archive()
        if data_archive_file_path is None:
            # No new files could be found
            return None

        # compare to file name rather than data location
        data_file = os.path.basename(os.path.normpath(data_archive_file_path))
        data_file_name = os.path.splitext(data_file)[0]

        last_database_run = self.get_most_recent_run_in_database()

        if last_database_run == data_file_name:
            logging.info(helper.RUN_MATCH_MSG, data_file_name, last_database_run)
            return True
        logging.warning(helper.RUN_MISMATCH_MSG, data_file_name, last_database_run)
        run_dict = self._construct_data_to_send(data_archive_file_path)
        self.resubmit_run_to_queue(run_dict)

    def resubmit_run_to_queue(self, run_dict):
        """
        Given a dictionary of run data, resubmit a run to the reduction Queue
        :param run_dict: A dictionary of run data generated by _construct_data_to_send
        """
        destination = '/queue/DataReady'
        logging.info(helper.DATA_SEND_LOG,
                     run_dict['rb_number'],
                     run_dict['instrument'],
                     run_dict['data'],
                     run_dict['run_number'],
                     run_dict['facility'])
        self.queue_session.send(destination, json.dumps(run_dict), priority='9')

    def _construct_data_to_send(self, run_data_loc):
        """
        This will construct the relevant data to be sent to the queue
        :param run_data_loc: The location in which the run is stored
        :return: A dictionary of values to send to the data processor queue
        """
        # Construct data
        run_number = self._get_run_number_from_file_path(run_data_loc)
        rb_number = self._get_rb_num(os.path.join(self.instrument_path,
                                                  'logs',
                                                  'journal'))
        return {
            "rb_number": rb_number,
            "instrument": self.instrument,
            "data": run_data_loc,
            "run_number": run_number,
            "facility": "ISIS"
        }

    def _find_most_recent_run_in_archive(self, current_cycle_path):
        """
        Given the most recent cycle path, find the most recent run
        :param current_cycle_path: full path to current cycle
        :return: The most recent file in the directory
        """
        base_dir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(current_cycle_path)
        all_files = os.listdir(current_cycle_path)
        time_filtered_files = self._filter_files_by_time(all_files, self._time_of_last_check)
        if not time_filtered_files:
            os.chdir(base_dir)
            logging.info(helper.NO_NEW_SINCE_LAST_MSG, self._time_of_last_check)
            return None

        def check_valid_extension(file_to_check):
            """
            Ensures that the extension of a particular file is either .nxs or .raw
            :return: True if the is .nxs/.raw
            """
            file_to_check = file_to_check.lower()
            if file_to_check.endswith('.raw') or file_to_check.endswith('.nxs'):
                return True
            return False

        # search all files in directory and return any that end in .raw or .RAW
        valid_files = [current_file for current_file in time_filtered_files
                       if check_valid_extension(current_file)]

        # sort all files by modified time
        valid_files.sort(key=os.path.getmtime)
        os.chdir(base_dir)
        try:
            return os.path.join(current_cycle_path, valid_files[-1])
        except IndexError:
            logging.warning(helper.NO_FILES_FOUND_MSG, current_cycle_path)
            return None

    @staticmethod
    def _filter_files_by_time(all_files, last_checked_time):
        """
        Removes any file from the list that has a modification
        time that is older than the last_checked_time
        :param all_files: List of all files to check
        :param last_checked_time: The cut off time for files we are interested in
        :return: list of files that does not contain any file which has a
                 most recent modification that was before the last_checked_time
        """
        new_files = []
        for current_file in all_files:
            modification_time = datetime.datetime.fromtimestamp(os.path.getmtime(current_file))
            if modification_time > last_checked_time:
                new_files.append(current_file)
        return new_files

    @staticmethod
    def _find_path_to_current_cycle_in_archive(instrument_data_path):
        """
        Finds the most recent cycle (current) by inspection of the instrument folder
        Assumes that most recent cycle folder is the final folder in directory
        :param instrument_data_path: The path to the instrument folder given as -
                                    \\\\isis\\inst$\\NDX%s\\Instrument\\data
        :return: The most recent cycle folder
        """
        all_folders = os.listdir(instrument_data_path)
        cycle_folders = sorted([folder for folder in all_folders if folder.startswith('cycle')])

        # List should have most recent cycle at the end
        return cycle_folders[-1]

    @staticmethod
    def _get_run_number_from_file_path(file_path):
        """
        Gets the run number of a file from it's name.
        :param file_path: The full file path to the run
                          assumes run file is the final file in the path
        :return: The run_number of a file
        """
        if os.path.isfile(file_path):
            file_name = os.path.basename(os.path.normpath(file_path))
            run_number = ''.join([num for num in file_name if num.isdigit()])
            if run_number == '':
                return None
            return run_number
        logging.error(helper.CANT_FIND_RUN_NUMBER_MSG, file_path)
        return None

    @staticmethod
    def _get_rb_num(instrument_summary_loc):
        """
        Reads last line of summary.txt file and returns the RB number.
        :param instrument_summary_loc: The location of the instrument summary directory
        :return the rb number for a run
        """
        if not os.path.isfile(os.path.join(instrument_summary_loc, 'summary.txt')):
            logging.error(helper.NO_SUMMARY_FILE, instrument_summary_loc)
            return None
        with open(os.path.join(instrument_summary_loc, 'summary.txt'), 'r') as summary:
            last_line = summary.readlines()[-1]
            if last_line.split()[-1].isdigit():
                return last_line.split()[-1]
            logging.error(helper.INVALID_JOURNAL_FORMAT_MSG)
            return None
