import time, Stomp_Client, json, twisted
#Config settings for cycle number, and instrument file arrangement
cycleNum = "14_3"
instrumentFile = "\\isis\inst$\NDXMERLIN\Instrument\data\cycle_14_3\%s.nxs"
activemq_client = Stomp_Client([("autoreduce.isis.cclrc.ac.uk", 61613)], 'autoreduce', '1^G8r2b$(6', 'RUN_BACKLOG')
activemq_client.connect()
        
        

class ISIS_Instrument_Monitor(object):
    def __init__(self, instrumType):
        self.InstrumentType = instrumType
        self.instrumentFile = self.setInstrumFile()
        self.instrumentSummaryLocat = self.instrumentFile + "\logs\journal\SUMMARY.txt"
        self.instrumentLastRunLocat = self.instrumentFile + "\logs\lastrun.txt"    
        
    def setInstrumFile(self):
        instrumentFolder = "\\isis\inst$\NDX%s\Instrument" % self.InstrumentType
        return instrumentFolder
        
    def queryBuilder(self):
        """ Uses information from lastRun file, 
        and last line of the summary text file to build the query 
        """ 
        lastRun = self.lastRunData.split()
        self.runNum = lastRun[1]
        lastSummary = self.lastSummary.split()
        self.RBNum = lastSummary[7]
        fileName = ''.join(lastRun[0:2]) #so MER111 etc
        self.runDataLocat = instrumentFile % fileName # need to chnge this

        
    def getRBNum(self):
        """ Reads last line of summary.txt file 
        """
        summaryTxt = self.instrumentSummaryLocat
        with open(summaryTxt, 'rb') as st:
            for line in st:
                pass
            self.lastSummary = line
        

    
    def writeToFile(self, dicto):
        """ Works as logger of dict files
        """
        with open("test.txt", 'w') as testtxt:
            testtxt.write(str(dicto))
    
        
    def messager(self):
        """Puts message together and sends it, along with logging
        """
        self.queryBuilder()
        data_dict = {
      "rb_number": self.RBNum,
      "instrument": "MERLIN",
      "data": self.runDataLocat,
      "run_number": self.runNum,
      "facility": "ISIS"
        }
        #activemq_client.send('/queue/DataReady', json.dumps(data_dict))
        print data_dict
        self.writeToFile(data_dict)
    
    def monitor(self):
        """ Works to actually monitor the file, like 'tail -f'
        """
        file = self.instrumentLastRunLocat
        file.seek(0,2)
        while True: #send thread to sleep, use Timer objects
            line = file.readline()
            if not line:
                time.sleep(0.1) 
                continue
            yield line
            line = self.lastRunData
            self.messager()
#instrumentName = "MERLIN"  
#lastSummary = "MER25101Adroja,             CeFe2Al10 40meV 200Hz 5K04-MAY-2015 16:52:39     6.9 1510145"  
#lastRun = "MER 25101 0"
logfile = open('lastrun.txt', 'r')
lastRun = monitor(logfile)    

