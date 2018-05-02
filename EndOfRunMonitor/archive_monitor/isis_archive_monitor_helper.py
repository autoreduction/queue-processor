"""
File to store messages and data relating to ISIS_archive_monitor
"""
import os

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import stomp

from EndOfRunMonitor.settings import ARCHIVE_MONITOR_LOG, MYSQL, INST_PATH, ACTIVEMQ

# ================================= Data ======================================= #

LOG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), ARCHIVE_MONITOR_LOG)
LOG_FORMAT = '%(asctime)s : %(message)s'

GENERIC_INST_PATH = INST_PATH

VALID_INST = ['GEM', 'POLARIS', 'WISH', 'MUSR', 'OSIRIS']

SLEEP_TIME = 600

DB_CONNECTION_STR = 'mysql+mysqldb://' + MYSQL['USER'] + ':' + MYSQL['PASSWD'] + \
                    '@' + MYSQL['HOST'] + '/' + MYSQL['DB']


# Database set up
def make_db_session():
    engine = create_engine(DB_CONNECTION_STR, pool_recycle=280)
    _ = MetaData(engine)
    session_maker = sessionmaker(bind=engine)
    return session_maker()


# Queue setup
def make_queue_session():
    brokers = [(ACTIVEMQ['brokers'].split(':')[0],
                int(ACTIVEMQ['brokers'].split(':')[1]))]
    connection = stomp.Connection(host_and_ports=brokers, use_ssl=False)
    connection.start()
    connection.connect(ACTIVEMQ['amq_user'],
                       ACTIVEMQ['amq_pwd'],
                       wait=False,
                       header={'activemq.prefetchSize': '1'})
    return connection


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

NO_NEW_SINCE_LAST_MSG = 'There are no new files since last check at %s'

CANT_FIND_RUN_NUMBER_MSG = 'Unable to find run number from file in path %s'

INVALID_JOURNAL_FORMAT_MSG = 'The journal summary file was not in the expected format. ' \
                             'The final value of each line should be the RB number.'

SLEEP_MSG = 'Archive Monitor will poll again in {} seconds.'.format(SLEEP_TIME)

CHECKING_INST_MSG = 'Performing Archive Check for %s'

STATUS_OF_CHECKS_MSG = '============= Checks %s for all instruments at %s =============='

NO_SUMMARY_FILE = 'Unable to find summary file at location %s.'
