import json, sys, re
from Stomp_Client import StompClient

# Config settings for cycle number, and instrument file arrangement
DATA_LOC = "\isis\NDX%s\Instrument\data\cycle_%s\\"
SUMMARY_LOC = "\logs\journal\SUMMARY.txt"
LAST_RUN_LOC = "\\\\isis\inst$\NDX%s\Instrument\logs\lastrun.txt"


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
    if not inp["max_run"] > inp["min_run"]:
        raise ValueError("Max run must be greater than min run")
    if not re.match(r"^\d\d_\d$", inp["cycle"]):
        raise ValueError("Cycle is not in the correct format")
    if not (inp["rename"] == "y" or inp["rename"] == "n"):
        raise ValueError("Nexus file rename requires y/n input")


def get_file_name_digits(instrument):
    """ This method scrapes the 'lastrun.txt' file on the instrument to find out the filenames of data files on that
    machine.
    """
    try:
        instrument_last_run = LAST_RUN_LOC % instrument
        with open(instrument_last_run) as f:
            data = get_data_and_check(f)
            return len(data[1])
    except Exception as e:
        print "Error reading last run file (%s)" % e
        print "Assuming eight numbers"
        return 8


def main():
    activemq_client = StompClient([("autoreduce.isis.cclrc.ac.uk", 61613)], 'autoreduce', 'xxxxxx', 'RUN_BACKLOG')
    activemq_client.connect()

    inp = {}

    if len(sys.argv) < 5:
        inp["inst_name"] = raw_input('Enter instrument name: ').upper()
        inp["min_run"] = int(raw_input('Start run number: '))
        inp["max_run"] = int(raw_input('End run number: '))
        inp["rename"] = raw_input('Use .nxs file? [Y/N]: ').lower()
        inp["rbnum"] = int(raw_input('RB Number: '))
        inp["cycle"] = raw_input('Enter cycle number in format [14_3]: ')
    else:
        inp["inst_name"] = str(sys.argv[1]).upper()
        inp["min_run"] = int(sys.argv[2])
        inp["max_run"] = int(sys.argv[3])
        inp["rename"] = 'n'  # change to use nxs file
        inp["rbnum"] = int(sys.argv[4])  # cast to int to test RB
        inp["cycle"] = str(sys.argv[5])

    validate_input(inp)

    data_filename_length = get_file_name_digits(inp["inst_name"])

    data_location = DATA_LOC % (inp["inst_name"], inp["cycle"])

    for run in range(inp["min_run"], inp["max_run"]+1):
        data_file = inp["inst_name"] + str(run).zfill(data_filename_length) + get_file_extension(inp["rename"])
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