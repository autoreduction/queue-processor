import time, json, os, logging, sys
from Stomp_Client import StompClient
import threading

# Config settings for cycle number, and instrument file arrangement
INST_FOLDER = "\\\\isis\inst$\NDX%s\Instrument"
DATA_LOC = "\data\cycle_%s\\"
SUMMARY_LOC = "\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = "\logs\lastrun.txt"
LOG_FILE = "xx\\monitor_log.txt"
INSTRUMENTS = [{'name': 'LET', 'use_nexus': True},
               {'name': 'MERLIN', 'use_nexus': False},
               {'name': 'MARI', 'use_nexus': False},
               {'name': 'MAPS', 'use_nexus': True},
               {'name': 'WISH', 'use_nexus': True},
               {'name': 'GEM', 'use_nexus': True}]
TIME_CONSTANT = 1  # Time between file reads (in seconds)
DEBUG = False
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')


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


class InstrumentMonitor(threading.Thread):
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
        self.instrumentDataFolderLoc = self.instrumentFolder + DATA_LOC % self._get_most_recent_cycle()
        self.lock = lock

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
        run_data_loc = self.instrumentDataFolderLoc + filename + get_file_extension(self.use_nexus)
        return {
            "rb_number": self._get_RB_num(),
            "instrument": self.instrumentName,
            "data": run_data_loc,
            "run_number": last_run_data[1],
            "facility": "ISIS"
        }

    def _get_RB_num(self):
        """ Reads last line of summary.txt file and returns the RB number
        """
        summary = self.instrumentSummaryLoc
        with open(summary, 'rb') as st:
            last_line = st.readlines()[-1]
            return last_line.split()[-1]

    def run(self):
        """ Works to actually monitor the last run file
        """
        try:
            with open(self.instrumentLastRunLoc) as lr:
                data = get_data_and_check(lr)
                last_run = data[1]

            while True:  # send thread to sleep, use Timer objects
                time.sleep(TIME_CONSTANT)
                with open(self.instrumentLastRunLoc) as lr:
                    data = get_data_and_check(lr)
                    if (data[1] != last_run) and (int(data[2]) == 0):
                        last_run = data[1]
                        self.send_message(data)

        except Exception as e:
            logging.exception("Error on loading file: ")
            raise e

    def send_message(self, last_run_data):
        """Puts message together and sends it, along with logging
        """
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
        file_monitor = InstrumentMonitor(inst['name'], inst['use_nexus'], activemq_client, message_lock)
        file_monitor.start()

if __name__ == "__main__":
    main()