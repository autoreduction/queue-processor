import time, json, datetime
from Stomp_Client import Stomp_Client

#Config settings for cycle number, and instrument file arrangement
CYCLE_NUM = "14_3"
INST_FOLDER = "\\isis\inst$\NDX%s\Instrument"
DATA_LOC = "\data\cycle_%s\\" % CYCLE_NUM
SUMMARY_LOC = "\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = "\logs\lastrun.txt"

class ISIS_Instrument_Monitor(object):
    def __init__(self, instrumentName, client):
        self.client = client
        self.instrumentName = instrumentName
        self.instrumentFolder = '.'
        #self.instrumentFolder = INST_FOLDER % self.instrumentName
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
        fileName = ''.join(lastRun[0:2]) #so MER111 etc
        self.runDataLocat = self.instrumentDataFolderLoc + fileName + ".nxs"

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
            file.seek(0, 2) #Go to end of file
            while True: #send thread to sleep, use Timer objects
                line = file.readline()
                if not line:
                    time.sleep(1)
                    continue
                self.lastRunData = line
                self.messager()

    def messager(self):
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
        #self.client.send('/queue/DataReady', json.dumps(data_dict))
        print data_dict
        self.writeToFile(data_dict)

activemq_client = Stomp_Client([("autoreduce.isis.cclrc.ac.uk", 61613)], 'autoreduce', '1^G8r2b$(6', 'RUN_BACKLOG')
activemq_client.connect()
file_monitor = ISIS_Instrument_Monitor('', activemq_client)
file_monitor.monitor()
