"""
Defines the InstrumentMonitor that watches files for updates in runs
"""
import json
import logging
import os
import threading

# pylint: disable=import-error
import stomp
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ICAT_Client import ICAT
from settings import ACTIVEMQ

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

# If True will check fake_archive folder for the last_run.txt file
# and will not send data to DataReady queue
USE_FAKE_ARCHIVE = False

logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    format='%(asctime)s %(message)s')

OBSERVER = Observer()


def get_file_extension(use_nxs):
    """ Choose the data extension based on the boolean"""
    if use_nxs:
        return ".nxs"
    return ".raw"


def get_data_and_check(last_run_file):
    """ Gets the data from the last run file and checks it's format """
    data = last_run_file.readline().split()
    if len(data) != 3:
        raise Exception("Unexpected last run file format")
    return data


# pylint: disable=too-many-instance-attributes
class InstrumentMonitor(FileSystemEventHandler):
    """
    Overides the FileSystemEventHandler to perform operations when
    """
    def __init__(self, instrument_name, use_nexus, client, lock):
        """
        :param instrument_name: name of the instrument
        :param use_nexus: if should use nexus format (bool)
        :param client: The ICAT client for ICAT access
        :param lock:
        """
        # pylint: disable=invalid-name
        self.icat = ICAT()
        super(InstrumentMonitor, self).__init__()
        self.client = client
        self.use_nexus = use_nexus
        self.instrumentName = instrument_name
        if USE_FAKE_ARCHIVE:
            self.instrumentFolder = "fake_archive\\" + self.instrumentName
        else:
            self.instrumentFolder = INST_FOLDER % self.instrumentName
        self.instrumentSummaryLoc = self.instrumentFolder + SUMMARY_LOC
        self.instrumentLastRunLoc = self.instrumentFolder + LAST_RUN_LOC
        with open(self.instrumentLastRunLoc) as last_run:
            data = get_data_and_check(last_run)
            self.last_run = data[1]
        self.lock = lock

    def _get_instrument_data_folder_loc(self, filename):
        """
        :param filename: name of file to use in generation of data location
        :return: directory containing instrument data
        """
        return self.instrumentFolder + DATA_LOC % self._get_most_recent_cycle(filename)

    def _get_most_recent_cycle(self, filename):
        """
        :param filename: name of a file from the most recent cycle
        :return: name of the most recent cycle
        """
        # Use an ICAT connection to get the most recent cycle
        cycle = self.icat.execute_query(QUERY.replace('{}', filename + ".raw"))
        # Retry and use an upper-case extension instead
        if not cycle:
            cycle = self.icat.execute_query(QUERY.replace('{}', filename + ".RAW"))
        # If there are no results, defer to previous method of finding the most recent folder
        if not cycle:
            folders = os.listdir(self.instrumentFolder + '\\logs\\')
            cycle_folders = [f for f in folders if f.startswith('cycle')]

            # List should have most recent cycle at the end
            most_recent = cycle_folders[-1]
        else:
            most_recent = cycle[0]

        return most_recent[most_recent.find('_')+1:]

    def build_dict(self, last_run_data):
        """
        Uses information from lastRun file,
        and last line of the summary text file to build the query
        """
        filename = ''.join(last_run_data[0:2])  # so MER111 etc
        run_data_loc = (self._get_instrument_data_folder_loc(filename)
                        + filename
                        + get_file_extension(self.use_nexus))
        return {
            "rb_number": self._get_rb_num(),
            "instrument": self.instrumentName,
            "data": run_data_loc,
            "run_number": last_run_data[1],
            "facility": "ISIS"
        }

    def _get_rb_num(self):
        """
        Reads last line of summary.txt file
        :return: the RB number
        """
        summary = self.instrumentSummaryLoc
        with open(summary, 'rb') as sum_file:
            last_line = sum_file.readlines()[-1]
            return last_line.split()[-1]

    def get_watched_folder(self):
        """
        :return: The log folder being watched
        """
        return self.instrumentFolder + '\\logs\\'

    # send thread to sleep, use Timer objects
    def on_modified(self, event):
        """
        Performs actions upon file modification
        :param event: The type of event taking place
        """
        try:
            # Storing folders into variables.
            list_of_folders = event.src_path.split("\\")
            # This will ensure to only execute the code for a specific file.
            if list_of_folders[-1] == "lastrun.txt":
                with open(self.instrumentLastRunLoc) as last_run:
                    data = get_data_and_check(last_run)
                # This code checks out the modified data and then it logs the changes.
                if (data[1] != self.last_run)and (int(data[2]) == 0):
                    self.last_run = data[1]
                    self.send_message(data)
        # pylint: disable=broad-except
        except Exception as exp:
            # if this code can't be executed it will raise a logging error towards the user.
            logging.exception("Error on loading file: %s ", exp.message, exc_info=True)

    def send_message(self, last_run_data):
        """
        Puts message together and sends it, along with logging.
        :param last_run_data: data from the last known run
        """
        with self.lock:
            data_dict = self.build_dict(last_run_data)
        if not USE_FAKE_ARCHIVE:
            self.client.send('/queue/DataReady', json.dumps(data_dict), priority='9')
        logging.info("Data sent: %s", str(data_dict))


def main():
    """
    Creates activeMQ connection and event handler
    :return:
    """
    brokers = [(ACTIVEMQ['brokers'].split(':')[0], int(ACTIVEMQ['brokers'].split(':')[1]))]
    connection = stomp.Connection(host_and_ports=brokers, use_ssl=False)
    logging.info("Starting ActiveMQ Connection")
    connection.start()
    logging.info("Completed ActiveMQ Connection")

    connection.connect(ACTIVEMQ['amq_user'],
                       ACTIVEMQ['amq_pwd'],
                       wait=False,
                       header={'activemq.prefetchSize': '1'})
    # ToDo: Is this still required
    # pylint: disable=pointless-string-statement
    '''
    for queue in ACTIVEMQ['amq_queues']:
        connection.subscribe(destination=queue,
                             id='1',
                             ack='client-individual',
                             header={'activemq.prefetchSize': '1'})
        logging.info("Subscribing to %s" % (queue))
    '''
    message_lock = threading.Lock()
    for inst in INSTRUMENTS:
        # Create an event_handler, this will decide what to do when files are changed.
        event_handler = InstrumentMonitor(inst['name'], inst['use_nexus'], connection, message_lock)
        # Watch the folder the program is in, it will pick up all changes made in the folder.
        path = event_handler.get_watched_folder()
        # Tell observer what to watch and give it the class that will handle the events.
        OBSERVER.schedule(event_handler, path)
    # Start watching files.
    OBSERVER.start()


def stop():
    """
    Disables the observer, it stop watching the files.
    """
    OBSERVER.stop()
    OBSERVER.join()


if __name__ == "__main__":
    main()
