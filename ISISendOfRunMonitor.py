import time, json, os, logging, sys
from Stomp_Client import StompClient
import threading

# Config settings for cycle number, and instrument file arrangement
CYCLE_NUM = "14_3"
INST_FOLDER = "\\\\isis\inst$\NDX%s\Instrument"
DATA_LOC = "\data\cycle_%s\\" % CYCLE_NUM
SUMMARY_LOC = "\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = "\logs\lastrun.txt"
LOG_FILE = "C:\\autoreduce\\scripts\\EndOfRunMonitor\\monitor_log.txt"
USE_NXS = True
INSTRUMENTS = ['LET']
TIME_CONSTANT = 1  # Time between file reads (in seconds)
DEBUG = False
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')


def get_file_extension():
    """ Choose the data extension based on the global boolean"""
    if USE_NXS:
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
    def __init__(self, instrument_name, client, lock):
        super(InstrumentMonitor, self).__init__()
        self.client = client
        self.instrumentName = instrument_name
        if DEBUG:
            self.instrumentFolder = '.'
        else:
            self.instrumentFolder = INST_FOLDER % self.instrumentName
        self.instrumentSummaryLoc = self.instrumentFolder + SUMMARY_LOC
        self.instrumentLastRunLoc = self.instrumentFolder + LAST_RUN_LOC
        self.instrumentDataFolderLoc = self.instrumentFolder + DATA_LOC
        self.lock = lock
        
    def build_dict(self, last_run_data):
        """ Uses information from lastRun file, 
        and last line of the summary text file to build the query 
        """
        filename = ''.join(last_run_data[0:2])  # so MER111 etc
        run_data_loc = self.instrumentDataFolderLoc + filename + get_file_extension()
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
            self.client.send('/queue/DataReady', json.dumps(data_dict))
        logging.info("Data sent: " + str(data_dict))


def main():
    activemq_client = StompClient([("autoreduce.isis.cclrc.ac.uk", 61613)], 'autoreduce', '1^G8r2b$(6', 'RUN_BACKLOG')
    activemq_client.connect()

    message_lock = threading.Lock()
    for inst in INSTRUMENTS:
        file_monitor = InstrumentMonitor(inst, activemq_client, message_lock)
        file_monitor.start()

if __name__ == "__main__":
    main()