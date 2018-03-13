#! /usr/bin/env python
from autoreduce_settings import ACTIVEMQ, MYSQL, ISIS_MOUNT
import MySQLdb
import MySQLdb.cursors
from os import path
import sys

'''
Compares the last run in the database to the lastrun.txt file
'''
def checkLastRun():
    db = MySQLdb.connect(host=MYSQL['host'], port=3306, user=MYSQL['username'], passwd=MYSQL['password'], db=MYSQL['db'], cursorclass=MySQLdb.cursors.DictCursor)
    cursor = db.cursor()
    
    # Get Instruments
    instruments = []
    cursor.execute("SELECT id, name FROM reduction_viewer_instrument WHERE is_active = 1 AND is_paused = 0")
    for i in cursor.fetchall():
        instruments.append(i)
        
    # Get last reduced datfile run number
    for inst in instruments:
        cursor.execute("SELECT MAX(run_number) FROM reduction_viewer_reductionrun WHERE instrument_id = " + str(inst['id']))
        last_reduction_run =  cursor.fetchone()['MAX(run_number)']
        file = open(path.join(ISIS_MOUNT, "NDX" + inst['name'], "Instrument", "logs", "lastrun.txt"), "r") 
        last_run = int(file.readline().split(' ')[1])
        
        # Check range because it may be a couple out.
        if(not last_reduction_run in range(last_run-2, last_run+2)):
            print("Last reduction run doesn't match lastrun.txt, check EndOfRunMonitor is running.")
            db.close()
            return 2
    db.close()
    return 0
    
if "__name__":
    sys.exit(checkLastRun())