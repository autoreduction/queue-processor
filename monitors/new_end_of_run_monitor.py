import csv
import logging
import os
import json
from filelock import (FileLock, Timeout)

from settings import (LAST_RUNS_CSV, CYCLE_FOLDER)

from utils.clients.queue_client import QueueClient
from utils.project.structure import get_log_file
from utils.project.static_content import LOG_FORMAT

# Setup logging
eorm_log = logging.getLogger('end_of_run_monitor')
eorm_log.setLevel(logging.INFO)

fh = logging.FileHandler(get_log_file('end_of_run_monitor.log'))
ch = logging.StreamHandler()
formatter = logging.Formatter(LOG_FORMAT)
fh.setFormatter(formatter)
ch.setFormatter(formatter)

eorm_log.addHandler(fh)
eorm_log.addHandler(ch)


class InstrumentMonitorError(Exception):
    pass


class FileNotFoundError(Exception):
    pass


def get_prefix_zeros(run_number_str):
    """
    Get the number of zeros prepended to a string
    :param run_number_str: Run number as a string
    :return: The zeros
    """
    zeros = ''
    for c in run_number_str:
        if c == '0':
            zeros += '0'
        else:
            return zeros


class InstrumentMonitor(object):
    """
    Checks the ISIS archive for new runs on an instrument and submits them to ActiveMQ
    """
    def __init__(self,
                 client,
                 instrument_name,
                 last_run_file,
                 summary_file,
                 data_dir,
                 file_ext):
        self.client = client
        self.instrument_name = instrument_name
        self.summary_file = summary_file
        self.last_run_file = last_run_file
        self.data_dir = data_dir
        self.file_ext = file_ext

    def read_instrument_last_run(self):
        """
        Read the last run recorded by the instrument from its lastrun.txt
        :return: Last run on the instrument as a string
        """
        with open(self.last_run_file, 'r') as fp:
            line_parts = fp.readline().split()
            if len(line_parts) != 3:
                raise InstrumentMonitorError("Unexpected last run file format for '{}'".format(self.last_run_file))
        return line_parts

    def read_rb_number_from_summary(self, run_number):
        """
        Loads the summary file and reads off the experiment RB number
        :param run_number: Run number to lookup
        :return: Experiment RB number
        """
        # Detect run number as a substring
        with open(self.summary_file, 'rb') as fp:
            for line in fp:
                line_parts = line.split()
                # Detect the run as a substring in summary.txt
                if str(run_number) in line_parts[0]:
                    # The last entry is the RB number
                    return line_parts[-1]
        raise InstrumentMonitorError("Unable to find run number in summary.txt '{}'".format(run_number))

    def build_dict(self, rb_number, run_number, file_location):
        """
        Build the data dictionary for a reduction job submission.
        :param rb_number: Experiment RB number
        :param run_number: Run number as it appears in lastrun.txt
        :param file_location: Absolute path to the data file
        :return: Data dictionary for submission
        """
        return self.client.serialise_data(rb_number=rb_number,
                                          instrument=self.instrument_name,
                                          location=file_location,
                                          run_number=run_number)

    def submit_run(self, rb_number, run_number, file_name):
        """
        Submit a run to ActiveMQ
        :param rb_number: RB number of the experiment
        :param run_number: Run number as it appears in lastrun.txt
        :param file_name: File name e.g. GEM1234.nxs
        """
        # Check to see if the last run exists, if not then raise an exception
        file_path = os.path.join(self.data_dir, CYCLE_FOLDER, file_name)

        if os.path.isfile(file_path):
            data_dict = self.build_dict(rb_number, run_number, file_path)
            self.client.send('/queue/DataReady', json.dumps(data_dict), priority='9')
        else:
            raise FileNotFoundError("File does not exist '{}'".format(file_path))

    def submit_run_difference(self, local_last_run):
        """
        Submit the difference between the last run on the archive for this
        instrument
        :param local_last_run: Local last run to check against
        """
        # Get archive lastrun.txt
        last_run_data = self.read_instrument_last_run()
        instrument_last_run = last_run_data[1]

        local_run_int = int(local_last_run)
        instrument_run_int = int(instrument_last_run)

        rb_number = self.read_rb_number_from_summary(str(instrument_run_int))
        zeros = get_prefix_zeros(instrument_last_run)
        if instrument_run_int > local_run_int:
            eorm_log.info("Submitting runs in range %i - %i", local_run_int, instrument_run_int)
            for i in range(local_run_int + 1, instrument_run_int + 1):
                # Construct the file name and run number
                run_number = zeros + str(i)
                file_name = last_run_data[0] + run_number + self.file_ext
                try:
                    self.submit_run(rb_number, run_number, file_name)
                except FileNotFoundError as ex:
                    # If the file isn't found then just return the last file sent
                    # and try again next time
                    eorm_log.error(ex.message)
                    return str(i - 1)
        return str(instrument_run_int)


def update_last_runs():
    """
    Read the last runs CSV file and bring it up to date with the
    instrument lastrun.txt
    """
    connection = QueueClient()

    # Loop over instruments
    output = []
    with open(LAST_RUNS_CSV, 'rb') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            inst_mon = InstrumentMonitor(connection,
                                         row[0],
                                         row[2],
                                         row[3],
                                         row[4],
                                         row[5])
            try:
                last_run = inst_mon.submit_run_difference(row[1])
                row[1] = last_run
            except InstrumentMonitorError as ex:
                eorm_log.error(ex.message)
            output.append(row)

    # Write any changes to the CSV
    with open(LAST_RUNS_CSV, 'wb') as csv_file:
        csv_writer = csv.writer(csv_file)
        for row in output:
            csv_writer.writerow(row)


def main():
    # Acquire a lock on the last runs CSV file to prevent access
    # by other instances of this script
    try:
        with FileLock("{}.lock".format(LAST_RUNS_CSV), timeout=1):
            update_last_runs()
    except Timeout:
        eorm_log.error(("Error acquiring lock on last runs CSV."
                        " There may be another instance running."))


if __name__ == '__main__':
    main()
