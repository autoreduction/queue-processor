"""
File to store messages and data relating to ISIS_archive_monitor
"""

from utils.settings import ARCHIVE_MONITOR_LOG, INST_PATH
# ================================= Data ======================================= #

LOG_FILE = ARCHIVE_MONITOR_LOG
LOG_FORMAT = '%(asctime)s : %(message)s'
STOMP_LOG_FORMAT = '%(asctime)s :      %(message)s'

GENERIC_INST_PATH = INST_PATH

VALID_INST = ['GEM', 'POLARIS', 'WISH', 'MUSR', 'OSIRIS']

SLEEP_TIME = 600


# ================================ Messages ===================================== #

INVALID_INSTRUMENT_MSG = 'Archive monitor could not be ' \
                         'started as %s was not recognised as a valid instrument. ' \
                         'If this is new, have you added it to the VALID_INST list?'

NO_INSTRUMENT_IN_DB_MSG = '     Returning None -- Unable to find instrument %s.'

NO_RUN_FOR_INSTRUMENT_MSG = '   Returning None -- Unable to find run for instrument: %s'

RUN_MISMATCH_MSG = '     Data Archive entry (%s) and Database entry (%s) did not match'

NO_FILES_FOUND_MSG = '     No files found when searching %s'

RUN_MATCH_MSG = '     Data Archive entry (%s) and Database entry (%s) matched!'

NO_NEW_SINCE_LAST_MSG = '     No new files since last check at %s'

CANT_FIND_RUN_NUMBER_MSG = '     Unable to find run number from file in path %s'

INVALID_JOURNAL_FORMAT_MSG = '     The journal summary file was not in the expected format. ' \
                             'The final value of each line should be the RB number.'

SLEEP_MSG = 'Archive Monitor will poll again in {} seconds.'.format(SLEEP_TIME)

CHECKING_INST_MSG = '%s:'

STATUS_OF_CHECKS_MSG = '============= Checks %s for all instruments at %s =============='

NO_SUMMARY_FILE = '     Unable to find summary file at location %s.'

DATA_SEND_LOG = '     Sending data:\n' \
                '                                   RB Number   = %s\n' \
                '                                   Instrument  = %s\n' \
                '                                   Data        = %s\n' \
                '                                   Run Number  = %s\n' \
                '                                   Facility    = %s'
