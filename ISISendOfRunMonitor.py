import time, json, datetime
from Stomp_Client import Stomp_Client

# Config settings for cycle number, and instrument file arrangement
CYCLE_NUM = "14_3"
INST_FOLDER = "\\isis\inst$\NDX%s\Instrument"
DATA_LOC = "\data\cycle_%s\\" % CYCLE_NUM
SUMMARY_LOC = "\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = "\logs\lastrun.txt"
USE_NXS = True
TIME_CONSTANT = 1  # Time between file reads (in seconds)

class ISIS_Instrument_Monitor(object):
    def __init__(self, instrumentName, client):
        self.client = client
        self.instrumentName = instrumentName
        self.instrumentFolder = '.'
        # self.instrumentFolder = INST_FOLDER % self.instrumentName
        self.instrumentSummaryLocat = self.instrumentFolder + SUMMARY_LOC
        self.instrumentLastRunLocat = self.instrumentFolder + LAST_RUN_LOC
        self.instrumentDataFolderLoc = self.instrumentFolder + DATA_LOC
        
    def queryBuilder(self):
        """ Uses information from lastRun file, 
        and last line of the summary text file to build the query 
        """ 
        lastRun = self.lastRunData.split()
        self.runNum = lastRun[1]
        self.RBNum = self._getRBNum()
        fileName = ''.join(lastRun[0:2])  # so MER111 etc
        self.runDataLocat = self.instrumentDataFolderLoc + fileName + self._get_file_extension()

    def _get_file_extension(self):
        """ Choose the data extension based on the global boolean"""
        if USE_NXS:
            return ".nxs"
        else:
            return ".raw"

    def _getRBNum(self):
        """ Reads last line of summary.txt file and returns the RB number
        """
        summaryTxt = self.instrumentSummaryLocat
        with open(summaryTxt, 'rb') as st:
            last_line = st.readlines()[-1]
            return last_line.split()[-1]

    def writeToFile(self, message):
        """ Works as logger of dict files
        """
        with open("monitor_log.txt", 'w') as log:
            log.write(str(datetime.datetime.now()) + ": ")
            log.write(str(message))

    def monitor(self):
        """ Works to actually monitor the file, like 'tail -f'
        """
        with open(self.instrumentLastRunLocat) as file:
            file.seek(0, 2)  # Go to end of file
            while True:  # send thread to sleep, use Timer objects
                line = file.readline()
                if not line:
                    time.sleep(TIME_CONSTANT)
                    continue
                if not self._has_ended(line):
                    file.seek(-len(line), 2)  # Move back a line
                    time.sleep(TIME_CONSTANT)
                    continue
                self.lastRunData = line
                self.send_message()

    def _has_ended(self, line):
        """ Function to check that the run has actually ended (runs with >0 in the line have only updated/stored)
        These are ignored for now but could be autoreduced eventually
        """
        if int(line.split()[-1]) == 0:
            return True
        else:
            return False

    def send_message(self):
        """Puts message together and sends it, along with logging
        """
        self.queryBuilder()
        data_dict = {
            "rb_number": self.RBNum,
            "instrument": self.instrumentName,
            "data": self.runDataLocat,
            "run_number": self.runNum,
            "facility": "ISIS"
        }
        # self.client.send('/queue/DataReady', json.dumps(data_dict))
        print data_dict
        self.writeToFile(data_dict)

activemq_client = Stomp_Client([("autoreduce.isis.cclrc.ac.uk", 61613)], 'autoreduce', '1^G8r2b$(6', 'RUN_BACKLOG')
activemq_client.connect()
file_monitor = ISIS_Instrument_Monitor('MERLIN', activemq_client)
file_monitor.monitor()
