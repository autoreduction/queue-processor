import time, json, datetime
from Stomp_Client import StompClient

# Config settings for cycle number, and instrument file arrangement
CYCLE_NUM = "14_3"
INST_FOLDER = "\\isis\inst$\NDX%s\Instrument"
DATA_LOC = "\data\cycle_%s\\" % CYCLE_NUM
SUMMARY_LOC = "\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = "\logs\lastrun.txt"
LOG_FILE = "monitor_log.txt"
USE_NXS = True
TIME_CONSTANT = 1  # Time between file reads (in seconds)


def get_file_extension():
    """ Choose the data extension based on the global boolean"""
    if USE_NXS:
        return ".nxs"
    else:
        return ".raw"


def write_to_log_file(message):
    """ Works as logger of dict files
    """
    with open(LOG_FILE, 'w') as log:
        log.write(str(datetime.datetime.now()) + ": ")
        log.write(str(message))


class InstrumentMonitor(object):
    def __init__(self, instrument_name, client):
        self.client = client
        self.instrumentName = instrument_name
        self.instrumentFolder = '.'
        # self.instrumentFolder = INST_FOLDER % self.instrumentName
        self.instrumentSummaryLoc = self.instrumentFolder + SUMMARY_LOC
        self.instrumentLastRunLoc = self.instrumentFolder + LAST_RUN_LOC
        self.instrumentDataFolderLoc = self.instrumentFolder + DATA_LOC
        
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

    def monitor(self):
        """ Works to actually monitor the last run file
        """
        with open(self.instrumentLastRunLoc) as lr:
            last_run = lr.readline().split()[1]
            while True:  # send thread to sleep, use Timer objects
                time.sleep(TIME_CONSTANT)
                lr.seek(0, 0)
                line = lr.readline()
                data = line.split()
                if (data[1] != last_run) and (int(data[2]) == 0):
                    last_run = data[1]
                    self.send_message(data)

    def send_message(self, last_run_data):
        """Puts message together and sends it, along with logging
        """
        data_dict = self.build_dict(last_run_data)
        # self.client.send('/queue/DataReady', json.dumps(data_dict))
        print data_dict
        write_to_log_file(data_dict)

activemq_client = StompClient([("autoreduce.isis.cclrc.ac.uk", 61613)], 'autoreduce', '1^G8r2b$(6', 'RUN_BACKLOG')
activemq_client.connect()
file_monitor = InstrumentMonitor('MERLIN', activemq_client)
file_monitor.monitor()
