import time, json, os, logging, sys
from Stomp_Client import StompClient
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Config settings for cycle number, and instrument file arrangement
INST_FOLDER = r"\\isis\inst$\NDX%s\Instrument"
DATA_LOC = r"\data\cycle_%s\\"
SUMMARY_LOC = r"\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = r"\logs\lastrun.txt"
LOG_FILE = r"xx\monitor_log.txt"
INSTRUMENTS = [{'name': 'LET', 'use_nexus': True},
               {'name': 'MERLIN', 'use_nexus': False},
               {'name': 'MAPS', 'use_nexus': True},
               {'name': 'WISH', 'use_nexus': True}]

TIME_CONSTANT = 1  # Time between file reads (in seconds)
DEBUG = False
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')
observer = Observer()


def get_file_extension(use_nxs):
    """ Choose the data extension based on the boolean"""
    if use_nxs:
        return ".nxs"
    else:
        return ".raw"


def get_data_and_check(last_run_file):
    """ Gets the data from the last run file and checks it's format """
    data = last_run_file.readline().split()
    if len(data) != 3:
        raise Exception("Unexpected last run file format")
    return data


class InstrumentMonitor(FileSystemEventHandler):

    def __init__(self, instrument_name, use_nexus, client, lock):
        super(InstrumentMonitor, self).__init__()
        self.client = client
        self.use_nexus = use_nexus
        self.instrumentName = instrument_name
        if DEBUG:
            self.instrumentFolder = '.\\' + self.instrumentName
        else:
            self.instrumentFolder = INST_FOLDER % self.instrumentName
        self.instrumentSummaryLoc = self.instrumentFolder + SUMMARY_LOC
        self.instrumentLastRunLoc = self.instrumentFolder + LAST_RUN_LOC
        with open(self.instrumentLastRunLoc) as lr:
            data = get_data_and_check(lr)
            self.last_run = data[1]
        self.lock = lock
        
    def _get_instrument_data_folder_loc(self):
        return self.instrumentFolder + DATA_LOC % self._get_most_recent_cycle()

    def _get_most_recent_cycle(self):
        folders = os.listdir(self.instrumentFolder + '\logs\\')
        cycle_folders = [f for f in folders if f.startswith('cycle')]

        # List should have most recent cycle at the end
        most_recent = cycle_folders[-1]
        return most_recent[most_recent.find('_')+1:]

    def build_dict(self, last_run_data):
        """ Uses information from lastRun file,
        and last line of the summary text file to build the query
        """
        filename = ''.join(last_run_data[0:2])  # so MER111 etc
        run_data_loc = self._get_instrument_data_folder_loc() + filename + get_file_extension(self.use_nexus)
        return {
            "rb_number": self._get_RB_num(),
            "instrument": self.instrumentName,
            "data": run_data_loc,
            "run_number": last_run_data[1],
            "facility": "ISIS"
        }

    def _get_RB_num(self):
        # Reads last line of summary.txt file and returns the RB number.
        summary = self.instrumentSummaryLoc
        with open(summary, 'rb') as st:
            last_line = st.readlines()[-1]
            return last_line.split()[-1]

    def get_watched_folder(self):
        return self.instrumentFolder + '\\logs\\'

    # send thread to sleep, use Timer objects
    def on_modified(self, event):
        try:
            # Storing folders into variables.
            list_of_folders = event.src_path.split("\\")
            # This will ensure to only execute the code for a specific file.
            if list_of_folders[-1] == "lastrun.txt":
                with open(self.instrumentLastRunLoc) as lr:
                    data = get_data_and_check(lr)
                # This code checks out the modified data and then it logs the changes.
                if (data[1] != self.last_run)and (int(data[2]) == 0):
                    self.last_run = data[1]
                    self.send_message(data)
        except Exception as e:
            # if this code can't be executed it will raise a logging error towards the user.
            logging.exception("Error on loading file: ", exc_info=True)

    def send_message(self, last_run_data):
        # Puts message together and sends it, along with logging.
        with self.lock:
            data_dict = self.build_dict(last_run_data)
        if not DEBUG:
            self.client.send('/queue/DataReady', json.dumps(data_dict), priority='9')
        logging.info("Data sent: " + str(data_dict))


def main():
    activemq_client = StompClient([("autoreduce.isis.cclrc.ac.uk", 61613)], 'autoreduce', 'xxxxxxxxx', 'RUN_BACKLOG')
    activemq_client.connect()

    message_lock = threading.Lock()
    for inst in INSTRUMENTS:

        # Create an event_handler, this will decide what to do when files are changed.
        event_handler = InstrumentMonitor(inst['name'], inst['use_nexus'], activemq_client, message_lock)
        # This will watch the folder the program is in, it will pick up all changes made in the folder.
        path = event_handler.get_watched_folder()
        # Tell the observer what to watch and give it the class that will handle the events.
        observer.schedule(event_handler, path)
        # Start watching files.
        observer.start()

def stop():
    # This function disables the observer, it stop watching the files.
    observer.stop()
    observer.join()

if __name__ == "__main__":
    main()

