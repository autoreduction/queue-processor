"""
End of run monitor. Detects new runs that arrive and
sends them off to the autoreduction service.
"""

import csv
import logging
import os
import json
import h5py
from filelock import (FileLock, Timeout)

from monitors.settings import (LAST_RUNS_CSV, CYCLE_FOLDER)

from utils.clients.queue_client import QueueClient
from utils.project.structure import get_log_file
from utils.project.static_content import LOG_FORMAT

# Setup logging
EORM_LOG = logging.getLogger('run_detection')
EORM_LOG.setLevel(logging.INFO)

FH = logging.FileHandler(get_log_file('run_detection.log'))
CH = logging.StreamHandler()
FORMATTER = logging.Formatter(LOG_FORMAT)
FH.setFormatter(FORMATTER)
FH.setFormatter(FORMATTER)

EORM_LOG.addHandler(FH)
EORM_LOG.addHandler(CH)


class InstrumentMonitorError(Exception):
    """
    Any fatal exception that occurs during execution of the
    instrument monitor
    """


def get_prefix_zeros(run_number_str):
    """
    Get the number of zeros prepended to a string
    :param run_number_str: Run number as a string
    :return: The zeros
    """
    zeros = ''
    for num in run_number_str:
        if num == '0':
            zeros += '0'
        else:
            return zeros
    return zeros


def read_rb_number_from_nexus_file(nxs_file_path):
    """
    Extract the experiment RB number from a Nexus file encoded
    in HDF5 format.
    :param nxs_file_path: Path to the Nexus file on disk
    :return: The RB number or None
    """
    try:
        nxs_file = h5py.File(nxs_file_path, mode="r")
    except IOError:
        # The most likely cause of this is the Nexus file being encoded
        # in HDF4 format.
        return None

    for (_, entry) in nxs_file.items():
        rb_number = entry.get('experiment_identifier').value[0]
        if rb_number:
            return str(rb_number, "utf-8")
    return None


class InstrumentMonitor:
    """
    Checks the ISIS archive for new runs on an instrument and submits them to ActiveMQ
    """
    def __init__(self, client, instrument_name):
        self.client = client
        self.instrument_name = instrument_name
        self.summary_file = ""
        self.last_run_file = ""
        self.data_dir = ""
        self.file_ext = ""

    def read_instrument_last_run(self):
        """
        Read the last run recorded by the instrument from its lastrun.txt
        :return: Last run on the instrument as a string
        """
        with open(self.last_run_file, 'r') as last_run:
            line_parts = last_run.readline().split()
            if len(line_parts) != 3:
                raise InstrumentMonitorError("Unexpected last run file format for '{}'"
                                             .format(self.last_run_file))
        return line_parts

    def read_rb_number_from_summary(self):
        """
        Loads the summary file and reads off the experiment RB number
        :return: Experiment RB number
        """
        with open(self.summary_file, 'rb') as summary:
            summary_lines = summary.readlines()
            last_line = summary_lines[-1]
            line_parts = last_line.split()
            if line_parts:
                return str(line_parts[-1], "utf-8")

        raise InstrumentMonitorError("Unable to read RB number from summary.txt")

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
                                          run_number=run_number,
                                          started_by=0)

    def submit_run(self, summary_rb_number, run_number, file_name):
        """
        Submit a run to ActiveMQ
        :param summary_rb_number: RB number of the experiment as read from the summary file
        :param run_number: Run number as it appears in lastrun.txt
        :param file_name: File name e.g. GEM1234.nxs
        """
        # Check to see if the last run exists, if not then raise an exception
        file_path = os.path.join(self.data_dir, CYCLE_FOLDER, file_name)

        if os.path.isfile(file_path):
            # Attempt to read an RB number from the Nexus file. This is most
            # useful for high frequency instruments like ENGINX where reading
            # from the summary is unreliable.
            rb_number = read_rb_number_from_nexus_file(file_path)
            if rb_number is None:
                rb_number = summary_rb_number
            EORM_LOG.info("Submitting '%s' with RB number '%s'", file_name, rb_number)
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

        summary_rb_number = self.read_rb_number_from_summary()
        zeros = get_prefix_zeros(instrument_last_run)
        if instrument_run_int > local_run_int:
            EORM_LOG.info("Submitting runs in range %i - %i for %s",
                          local_run_int,
                          instrument_run_int,
                          self.instrument_name)
            for i in range(local_run_int + 1, instrument_run_int + 1):
                # Construct the file name and run number
                run_number = zeros + str(i)
                file_name = last_run_data[0] + run_number + self.file_ext
                try:
                    self.submit_run(summary_rb_number, run_number, file_name)
                except FileNotFoundError as ex:
                    # If the file isn't found then just return the last file sent
                    # and try again next time
                    EORM_LOG.error(ex)
                    return str(i - 1)
        return str(instrument_run_int)


def update_last_runs(csv_name):
    """
    Read the last runs CSV file and bring it up to date with the
    instrument lastrun.txt
    :param csv_name: File name of the local last runs CSV file
    """
    connection = QueueClient()

    # Loop over instruments
    output = []
    with open(csv_name, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            inst_mon = InstrumentMonitor(connection, row[0])
            inst_mon.last_run_file = row[2]
            inst_mon.summary_file = row[3]
            inst_mon.data_dir = row[4]
            inst_mon.file_ext = row[5]

            try:
                last_run = inst_mon.submit_run_difference(row[1])
                row[1] = last_run
            except InstrumentMonitorError as ex:
                EORM_LOG.error(ex)
            output.append(row)

    # Write any changes to the CSV
    with open(csv_name, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        for row in output:
            csv_writer.writerow(row)


def main():
    """
    EoRM entry point
    """
    # Acquire a lock on the last runs CSV file to prevent access
    # by other instances of this script
    try:
        with FileLock("{}.lock".format(LAST_RUNS_CSV), timeout=1):
            update_last_runs(LAST_RUNS_CSV)
    except Timeout:
        EORM_LOG.error(("Error acquiring lock on last runs CSV."
                        " There may be another instance running."))


if __name__ == '__main__':
    main()
