"""
This script periodically checks the lastrun.txt file on selected instruments and sends a message to
the DataReady queue when runs end.
"""
import json
import logging
import os
import threading
import csv

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from monitors.settings import (INST_FOLDER, DATA_LOC, SUMMARY_LOC,
                               LAST_RUN_LOC, EORM_LOG_FILE, INSTRUMENTS,
                               EORM_LAST_RUN_FILE)
from utils.clients.queue_client import QueueClient

logging.basicConfig(filename=EORM_LOG_FILE,
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s')
observer = Observer()  # pylint: disable=invalid-name

def write_last_run(file_name, instrument, last_run):
    """
    Write the last run for an instrument to the last runs CSV file
    """
    try:
        # Attempt to open and read the CSV file
        with open(file_name, 'rb') as last_run_file:
            last_run_rows = []
            last_run_reader = csv.reader(last_run_file)
            found_inst = False
            # Attempt to find the instrument in the CSV file
            for row in last_run_reader:
                if row[0] == instrument:
                    row[1] = last_run
                    found_inst = True
                last_run_rows.append(row)

            # If the instrument isn't found, then we need to add it
            if not found_inst:
                row = [instrument, last_run]
                last_run_rows.append(row)
    except IOError:
        # File hasn't been created yet
        last_run_rows = [[instrument, last_run]]

    # Write each row of the CSV back to the file
    last_run_file = open(file_name, 'wb+')
    last_run_writer = csv.writer(last_run_file)
    for row in last_run_rows:
        last_run_writer.writerow(row)
    last_run_file.close()

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
        super(InstrumentMonitor, self).__init__()
        self.client = client
        self.use_nexus = use_nexus
        self.instrument_name = instrument_name
        self.instrument_folder = INST_FOLDER % self.instrument_name
        self.instrument_summary_loc = os.path.join(self.instrument_folder, SUMMARY_LOC)
        self.instrument_last_run_loc = os.path.join(self.instrument_folder, LAST_RUN_LOC)
        with open(self.instrument_last_run_loc) as lastrun:
            data = get_data_and_check(lastrun)
            self.last_run = data[1]
        self.lock = lock

    def _get_instrument_data_folder_loc(self):
        """ Gets instrument data folder location. """
        return os.path.join(self.instrument_folder, DATA_LOC % self._get_most_recent_cycle())

    def _get_most_recent_cycle(self):
        """
        Look at the logs folder to determine the current cycle.
        :return: A 4 character cycle string e.g. '18_1'
        """
        folders = os.listdir(os.path.join(self.instrument_folder, 'logs'))
        cycle_folders = [f for f in folders if f.startswith('cycle')]
        cycle_folders.sort()

        # List should have most recent cycle at the end
        most_recent = cycle_folders[-1]
        cycle = most_recent[most_recent.find('_') + 1:]
        logging.debug("Found most recent cycle to be %s", cycle)
        return cycle

    def build_dict(self, last_run_data):
        """ Uses information from lastRun file,
        and last line of the summary text file to build the query
        """
        filename = ''.join(last_run_data[0:2])  # so MER111 etc
        filename += get_file_extension(self.use_nexus)
        run_data_loc = os.path.join(self._get_instrument_data_folder_loc(),
                                    filename)
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
            logging.debug("RB number found to be %s", str(last_line.split()[-1]))
            return last_line.split()[-1]

    def get_watched_folder(self):
        """ Returns the watched folder location. """
        return os.path.join(self.instrument_folder, 'logs')

    # send thread to sleep, use Timer objects
    def on_modified(self, event):
        """ Handler when last_run.txt modified event received. """
        try:
            logging.debug("Received modified from %s", str(event.src_path))
            # Storing folders into variables.
            if os.name == "nt":
                list_of_folders = event.src_path.split("\\")
            else:
                list_of_folders = event.src_path.split("/")
            # This will ensure to only execute the code for a specific file.
            if list_of_folders[-1] == "lastrun.txt":
                with open(self.instrument_last_run_loc) as lastrun:
                    data = get_data_and_check(lastrun)
                # This code checks out the modified data and then it logs the changes.
                logging.debug("data[1] = %s self.last_run = %s", str(data[1]), str(self.last_run))
                if (data[1] != self.last_run) and (int(data[2]) == 0):
                    self.last_run = data[1]
                    logging.debug("self.last_run updated to be %s", str(data[1]))
                    self.send_message(data)
                    # Write to the last runs file for the health checker
                    write_last_run(EORM_LAST_RUN_FILE, self.instrument_name, self.last_run)
        except Exception as exp:  # pylint: disable=broad-except
            # if this code can't be executed it will raise a logging error towards the user.
            logging.exception("Error on loading file: %s", exp.message, exc_info=True)

    def send_message(self, last_run_data):
        """ Puts message together and sends it to queue. """
        with self.lock:
            data_dict = self.build_dict(last_run_data)
        self.client.send('/queue/DataReady', json.dumps(data_dict), priority='9')
        logging.info("Data sent: %s", str(data_dict))


def main():
    """ Main method, connects to ActiveMQ and sets up instrument last_run.txt listeners. """
    logging.info("Connecting to ActiveMQ...")
    connection = QueueClient()
    logging.info("Connected to ActiveMQ")

    message_lock = threading.Lock()
    for inst in INSTRUMENTS:
        # Create an event_handler, this will decide what to do when files are changed.
        event_handler = InstrumentMonitor(inst['name'], inst['use_nexus'], connection, message_lock)
        # This will watch the folder the program is in and pick up all changes made in the folder.
        path = event_handler.get_watched_folder()
        # Tell the observer what to watch and give it the class that will handle the events.
        observer.schedule(event_handler, path)
        logging.info("Watching %s", str(path))
    # Start watching files.
    observer.start()


def stop():
    """ This function disables the observer, stop watching the last run files. """
    observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
