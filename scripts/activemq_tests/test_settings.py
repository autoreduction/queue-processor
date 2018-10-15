# pylint: skip-file
import os

from utils.project.structure import get_log_folder


LOG_FILENAME = os.path.join(get_log_folder(), 'test_logging.out')

# ActiveMQ

ACTIVEMQ = {
    'username': 'admin',
    'password': 'password',
    'broker': [('127.0.1.1', 61613)],
    'SSL': False
}
