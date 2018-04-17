"""
File to store messages and data relating to ISIS_archive_monitor
"""
import os

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from settings import ARCHIVE_MONITOR_LOG, MYSQL, INST_PATH

# ================================= Data ======================================= #

LOG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), ARCHIVE_MONITOR_LOG)

GENERIC_INST_PATH = INST_PATH

VALID_INST = ['GEM', 'POLARIS', 'WISH', 'TEST']

DB_CONNECTION_STR = 'mysql+mysqldb://' + MYSQL['USER'] + ':' + MYSQL['PASSWD'] + \
                    '@' + MYSQL['HOST'] + '/' + MYSQL['DB']

# Database set up
ENGINE = create_engine(DB_CONNECTION_STR, pool_recycle=280)
_ = MetaData(ENGINE)
session = sessionmaker(bind=ENGINE)
SESSION = session()

# ================================ Messages ===================================== #

START_UP_MSG = 'Starting new Archive Monitor for instrument: %s'

INVALID_INSTRUMENT_MSG = 'ISIS_archive_monitor.__init__: Archive monitor could not be ' \
                         'started as %s was not recognised as a valid instrument. ' \
                         'If this is new, have you added it to the VALID_INST list?'

NO_INSTRUMENT_IN_DB_MSG = 'ISIS_archive_monitor.get_most_recent_run_in_database: ' \
                          'Returning None -- Unable to find instrument %s.'

NO_RUN_FOR_INSTRUMENT_MSG = 'ISIS_archive_monitor.get_most_recent_run_in_database: ' \
                            'Returning None -- Unable to find run for instrument: %s'

RUN_MISMATCH_MSG = 'ISIS_archive_monitor.compare_most_recent_to_reduction_db: ' \
                   'Data Archive entry (%s) and Database entry (%s) did not match'

NO_FILES_FOUND_MSG = 'No files found when searching %s'

RUN_MATCH_MSG = 'ISIS_archive_monitor.compare_most_recent_to_reduction_db: ' \
                'Data Archive entry (%s) and Database entry (%s) matched! ' \
                'No further action required.'
