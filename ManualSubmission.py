import json, sys, re
import xml.etree.ElementTree as ET
from Stomp_Client import StompClient
from ICAT_Client import ICAT

# Config settings for cycle number, and instrument file arrangement
DATA_LOC = "\isis\NDX%s\Instrument\data\cycle_%s\\"
SUMMARY_LOC = "\\\\isis\inst$\NDX%s\Instrument\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = "\\\\isis\inst$\NDX%s\Instrument\logs\lastrun.txt"

RB_QUERY = "SELECT investigation FROM Investigation investigation JOIN " + \
           "investigation.datasets dataset JOIN dataset.datafiles datafile " + \
           "WHERE datafile.name LIKE '{}%'"

CYCLE_QUERY = "SELECT facilityCycle.name FROM FacilityCycle facilityCycle JOIN"+\
              " facilityCycle.facility facility JOIN facility.investigations "+\
              "investigation WHERE investigation.id = '{}' AND investigation.startDate " + \
              "BETWEEN facilityCycle.startDate AND facilityCycle.endDate"

def lookup_rb_number(instrument, run_number, icat, icat_client):
    """ Uses the summary.txt file to attempt to lookup the run's RB number.
    Beware that there are issues with summary.txt:
    * RB numbers changed in ICAT after the fact are not updated here
    * Run numbers are truncated to 5 digits and so are modulo 100000
    To be safe this function is written to fail as much as possible
    """
    run_string = str(run_number)
    print "Attempting to lookup RB number in ICAT"
    try:
        # Try looking in ICAT for the RB number first
        rb_number = icat.execute_query(icat_client, RB_QUERY.replace('{}', instrument.upper() + run_string))
        
        # If we haven't found an RB number, we must redo the search but with the run number having leading zeros
        if rb_number == []:
            print 'Adding leading zeros to the run number'
            while len(run_string) < 8:
                run_string = "0" + run_string
            rb_number = icat.execute_query(icat_client, RB_QUERY.replace('{}', instrument.upper() + run_string))
            
            # If we still haven't found the RB number, we can search the SUMMARY text file instead
            if rb_number == []:
                print 'Searching SUMMARY.txt instead'
                run_number_mod = run_number % 100000
                rb_number = -1
                with open(SUMMARY_LOC % instrument) as f:
                    for line in f.readlines():
                        summary_run = int(line[3:8])
                        if summary_run == run_number_mod:
                            if rb_number != -1:
                                # Run not unique in file, fail
                                return -1
                            else:
                                rb_number = line[-8:-1]
        
        if not isinstance(rb_number, str): 
            rb_number = rb_number[0]

    except Exception as e:
        print "RB not found (%s)" % e
        rb_number = -1

    return rb_number


def get_cycle(investigation_id, icat, icat_client):
    """ Finds the cycle automatically in ICAT to save the user typing it in """
    print "Attempting to lookup cycle in ICAT"
    # Try looking in ICAT for the RB number first
    try:
        cycle = icat.execute_query(icat_client, CYCLE_QUERY.replace('{}', investigation_id))[0]
        cycle = cycle.replace('cycle_', '')
        
        if cycle != None:
            print 'Found cycle to be ' + cycle
    # This can happen when runs are outside of the official listings for cycle
    # dates. This usually happens where there is no beam but runs are sent
    # through to ICAT anyway. In this case, default to asking the user for the cycle
    except Exception as e:
        print "Cycle not found in ICAT(%s)" % e
        cycle = None
    return cycle
    

def get_file_extension(use_nxs):
    """ Choose the data extension based on the boolean"""
    if use_nxs == "y":
        return ".nxs"
    else:
        return ".raw"


def get_data_and_check(last_run_file):
    """ Gets the data from the last run file and checks it's format """
    data = last_run_file.readline().split()
    if len(data) != 3:
        raise Exception("Unexpected last run file format")
    return data


def validate_input(inp):
    if not inp["inst_name"].isalpha():
        raise ValueError("Invalid instrument name")
    if not inp["max_run"] >= inp["min_run"]:
        raise ValueError("Max run must be greater or equal to min run")
    if not re.match(r"^\d\d_\d$", inp["cycle"]):
        raise ValueError("Cycle is not in the correct format")
    if not (inp["rename"] == "y" or inp["rename"] == "n"):
        raise ValueError("Nexus file rename requires y/n input")


def get_file_name_data(instrument):
    """ This method scrapes the 'lastrun.txt' file on the instrument to find out the filenames of data files on that
    machine.
    """
    try:
        instrument_last_run = LAST_RUN_LOC % instrument
        with open(instrument_last_run) as f:
            data = get_data_and_check(f)
            return (data[0], len(data[1]))
    except Exception as e:
        print "Error reading last run file (%s)" % e
        print "Assuming eight numbers and first three chars of instrument"
        return (instrument[0:3], 8)


def main():
    print "Connecting to ActiveMQ"
    # Connect to ActiveMQ
    activemq_client = StompClient([("autoreducedev2.isis.cclrc.ac.uk", 61613)], 'autoreduce', 'activedev', 'RUN_BACKLOG')
    activemq_client.connect()

    print "Connecting to ICAT"
    # Connect to ICAT
    icat = ICAT()
    icat_client = icat.get_client()
    
    inp = {}
    if len(sys.argv) < 5:
        inp["inst_name"] = raw_input('Enter instrument name: ').upper()
        inp["min_run"] = int(raw_input('Start run number: '))
        inp["max_run"] = int(raw_input('End run number: '))
        inp["rename"] = raw_input('Use .nxs file? [Y/N]: ').lower()
        inp["rbnum"] = lookup_rb_number(inp["inst_name"], inp["min_run"], icat, icat_client)  # Assume all RBs are the same as the first
        if inp["rbnum"] == -1:
            print "Lookup failed"
            inp["rbnum"] = int(raw_input('RB Number: '))
        else:
            if not isinstance(inp["rbnum"], str):
                investigation_id = str(inp["rbnum"].id)
                inp["rbnum"] = str(inp["rbnum"].name)
            print "Found rb number: " + str(inp["rbnum"])
        if investigation_id != None:
            inp["cycle"] = get_cycle(investigation_id, icat, icat_client)
        # If we couldn't find the cycle in ICAT, ask the user for the cycle
        if inp["cycle"] == None:
            inp["cycle"] = raw_input('Enter cycle number in format [14_3]: ')
    else:
        inp["inst_name"] = str(sys.argv[1]).upper()
        inp["min_run"] = int(sys.argv[2])
        inp["max_run"] = int(sys.argv[3])
        inp["rename"] = 'n'  # change to use nxs file
        inp["rbnum"] = int(sys.argv[4])  # cast to int to test RB
        inp["cycle"] = str(sys.argv[5])

    validate_input(inp)

    data_file_prefix, data_filename_length = get_file_name_data(inp["inst_name"])

    data_location = DATA_LOC % (inp["inst_name"], inp["cycle"])

    # Search through the mapping file to find the corresponding shortcode for the instrument name that we have chosen.		
    # This is necessary due to the difference in the nomenclature of entities at the instrument and datafile level		
    tree = ET.parse('InstrumentMapping.xml')		
    root = tree.getroot()		
    for child in root:		
        if child.find('longname').text == inp["inst_name"]:		
            # Save the shortcode that will be used to find the datafile and break as we've found what we needed.		
            instrument_long = inp["inst_name"]
            instrument_short = child.find('shortcode').text
            break
        elif child.find('shortcode').text == inp["inst_name"]:
            instrument_long = child.find('longcode').text
            instrument_short = inp["inst_name"]

    for run in range(inp["min_run"], inp["max_run"]+1):
        data_file = instrument_short + str(run).zfill(data_filename_length) + get_file_extension(inp["rename"])
        print 'Creating a job for the datafile at: ' + data_file
        data_dict = {
            "rb_number": str(inp["rbnum"]),
            "instrument": inp["inst_name"],
            "data": data_location + data_file,
            "run_number": str(int(run)),
            "facility": "ISIS"
            }
        activemq_client.send('/queue/DataReady', json.dumps(data_dict), priority=1)
        print data_dict

if __name__ == "__main__":
    main()
