"""
This script periodically checks the lastrun.txt file on selected instruments and sends a message to
the DataReady queue when runs end.
"""
import json
import os
import logging
import threading
import stomp

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from EndOfRunMonitor.ICAT_Client import ICAT
from EndOfRunMonitor.settings import ACTIVEMQ

# Config settings for cycle number, and instrument file arrangement
INST_FOLDER = r"\\isis\inst$\NDX%s\Instrument"
DATA_LOC = r"\data\cycle_%s\\"
SUMMARY_LOC = r"\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = r"\logs\lastrun.txt"
LOG_FILE = r"monitor_log.txt"
INSTRUMENTS = [{'name': 'WISH', 'use_nexus': True}]

QUERY = "SELECT facilityCycle.name FROM FacilityCycle facilityCycle, \
         facilityCycle.facility as facility, facility.investigations as \
         investigation, investigation.datasets as dataset, dataset.datafiles \
         as datafile WHERE datafile.name = '{}' AND \
         datafile.datafileCreateTime BETWEEN facilityCycle.startDate AND \
         facilityCycle.endDate"

# Check fake_archive folder for the last_run.txt file and will not send data to DataReady queue"
USE_FAKE_ARCHIVE = False

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')
observer = Observer() # pylint: disable=invalid-name


def get_file_extension(use_nxs):
    """ Choose the data extension based on the boolean. """
    if use_nxs:
        return ".nxs"
    return ".raw"


def get_data_and_check(last_run_file):
    """ Gets the data from the last run file and checks it's format. """
    data = last_run_file.readline().split()
    if len(data) != 3:
        raise Exception("Unexpected last run file format")
    return data


class InstrumentMonitor(FileSystemEventHandler):
    """ This is the event handler class for the lastrun.txt file. """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, instrument_name, use_nexus, client, lock):
        self.icat = ICAT()
        super(InstrumentMonitor, self).__init__()
        self.client = client
        self.use_nexus = use_nexus
        self.instrument_name = instrument_name
        if USE_FAKE_ARCHIVE:
            self.instrument_folder = "fake_archive\\" + self.instrument_name
        else:
            self.instrument_folder = INST_FOLDER % self.instrument_name
        self.instrument_summary_loc = self.instrument_folder + SUMMARY_LOC
        self.instrument_last_run_loc = self.instrument_folder + LAST_RUN_LOC
        with open(self.instrument_last_run_loc) as lastrun:
            data = get_data_and_check(lastrun)
            self.last_run = data[1]
        self.lock = lock

    def _get_instrument_data_folder_loc(self, filename):
        """ Gets instrument data folder location. """
        return self.instrument_folder + DATA_LOC % self._get_most_recent_cycle(filename)

    def _get_most_recent_cycle(self, filename):
        """ Use an ICAT connection to get the most recent cycle. """
        cycle = self.icat.execute_query(QUERY.replace('{}', filename + ".raw"))
        # Retry and use an upper-case extension instead
        if not cycle:
            cycle = self.icat.execute_query(QUERY.replace('{}', filename + ".RAW"))
        # If there are no results, defer to previous method of finding the most recent folder
        if not cycle:
            folders = os.listdir(self.instrument_folder + r'\logs\\')
            cycle_folders = [f for f in folders if f.startswith('cycle')]

            # List should have most recent cycle at the end
            most_recent = cycle_folders[-1]
        else:
            most_recent = cycle[0]

        return most_recent[most_recent.find('_') + 1:]

    def build_dict(self, last_run_data):
        """ Uses information from lastRun file,
        and last line of the summary text file to build the query
        """
        filename = ''.join(last_run_data[0:2])  # so MER111 etc
        run_data_loc = self._get_instrument_data_folder_loc(filename) + filename + \
                       get_file_extension(self.use_nexus)
        return {
            "rb_number": self._get_rb_num(),
            "instrument": self.instrument_name,
            "data": run_data_loc,
            "run_number": last_run_data[1],
            "facility": "ISIS"
        }

    def _get_rb_num(self):
        """ Reads last line of summary.txt file and returns the RB number. """
        with open(self.instrument_summary_loc, 'rb') as summary:
            last_line = summary.readlines()[-1]
            return last_line.split()[-1]

    def get_watched_folder(self):
        """ Returns the watched folder location. """
        return self.instrument_folder + '\\logs\\'

    # send thread to sleep, use Timer objects
    def on_modified(self, event):
        """ Handler when last_run.txt modified event received. """
        try:
            # Storing folders into variables.
            list_of_folders = event.src_path.split("\\")
            # This will ensure to only execute the code for a specific file.
            if list_of_folders[-1] == "lastrun.txt":
                with open(self.instrument_last_run_loc) as lastrun:
                    data = get_data_and_check(lastrun)
                # This code checks out the modified data and then it logs the changes.
                if (data[1] != self.last_run) and (int(data[2]) == 0):
                    self.last_run = data[1]
                    self.send_message(data)
        except Exception as exp:  # pylint: disable=broad-except
            # if this code can't be executed it will raise a logging error towards the user.
            logging.exception("Error on loading file: %s", exp.message, exc_info=True)

    def send_message(self, last_run_data):
        """ Puts message together and sends it to queue. """
        with self.lock:
            data_dict = self.build_dict(last_run_data)
        if not USE_FAKE_ARCHIVE:
            self.client.send('/queue/DataReady', json.dumps(data_dict), priority='9')
        logging.info("Data sent: %s", str(data_dict))


def main():
    """ Main method, connects to ActiveMQ and sets up instrument last_run.txt listeners. """
    brokers = [(ACTIVEMQ['brokers'].split(':')[0], int(ACTIVEMQ['brokers'].split(':')[1]))]
    connection = stomp.Connection(host_and_ports=brokers, use_ssl=False)
    logging.info("Starting ActiveMQ Connection")
    connection.start()
    logging.info("Completed ActiveMQ Connection")

    connection.connect(ACTIVEMQ['amq_user'],
                       ACTIVEMQ['amq_pwd'],
                       wait=False,
                       header={'activemq.prefetchSize': '1'})

    message_lock = threading.Lock()
    for inst in INSTRUMENTS:
        # Create an event_handler, this will decide what to do when files are changed.
        event_handler = InstrumentMonitor(inst['name'], inst['use_nexus'], connection, message_lock)
        # This will watch the folder the program is in and pick up all changes made in the folder.
        path = event_handler.get_watched_folder()
        # Tell the observer what to watch and give it the class that will handle the events.
        observer.schedule(event_handler, path)
    # Start watching files.
    observer.start()


def stop():
    """ This function disables the observer, stop watching the last run files. """
    observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
