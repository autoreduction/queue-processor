import csv
import os
import logging
from filelock import (FileLock, Timeout)
from settings import (CYCLE_FOLDER, LAST_RUNS_CSV)

from utils.project.structure import get_log_file
from utils.project.static_content import LOG_FORMAT
logging.basicConfig(filename=get_log_file('end_of_run_monitor.log'), level=logging.INFO,
                    format=LOG_FORMAT)


class InstrumentMonitorError(Exception):
    pass


class InstrumentMonitor(object):
    """
    Checks the ISIS archive for new runs on an instrument and submits them to ActiveMQ
    """
    def __init__(self, instrument_name, last_run_file, summary_file, data_dir):
        self.instrument_name = instrument_name
        self.summary_file = summary_file
        self.last_run_file = last_run_file
        self.data_dir = data_dir

    def read_instrument_last_run(self):
        """
        Read the last run recorded by the instrument from its lastrun.txt
        :return: Last run on the instrument as an integer
        """
        with open(self.last_run_file, 'r') as fp:
            line_parts = fp.readline().split()
            if len(line_parts) != 3:
                raise InstrumentMonitorError("Unexpected last run file format for '{}'".format(self.last_run_file))
            last_run = int(line_parts[1])
        return last_run

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

    def submit_run(self, run_number):
        """
        Submit a run to ActiveMQ
        :param run_number: Particular run to submit
        """
        # Check to see if the last run exists, if not then raise an exception

        # Submit run to ActiveMQ
        return None

    def submit_run_difference(self, local_last_run):
        """
        Submit the difference between the last run on the archive for this
        instrument
        :param local_last_run: Local last run to check against
        """
        # Get archive lastrun.txt
        instrument_last_run = self.read_instrument_last_run()
        rb_number = self.read_rb_number_from_summary(instrument_last_run)
        print("Instrument last run is %s" % instrument_last_run)
        print("RB number is %s" % rb_number)


def update_last_runs():
    # Loop over instruments
    with open(LAST_RUNS_CSV, 'rb') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            inst_mon = InstrumentMonitor(row[0], row[2], row[3], row[4])
            try:
                inst_mon.submit_run_difference(row[1])
            except InstrumentMonitorError as ex:
                logging.error(ex.message)


def main():
    # Acquire a lock on the last runs CSV file to prevent access
    # by other instances of this script
    try:
        with FileLock("{}.lock".format(LAST_RUNS_CSV), timeout=1):
            update_last_runs()
    except Timeout:
        logging.warn(("Error acquiring lock on last runs CSV."
                      " There may be another instance running."))


if __name__ == '__main__':
    main()