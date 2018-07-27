# pylint: skip-file
"""
Settings for connecting to the test services that run locally
"""
import os

ICAT = {
    'AUTH': 'YOUR-ICAT-AUTH-TYPE',
    'URL': 'YOUR-ICAT-WSDL-URL',
    'USER': 'YOUR-ICAT-USERNAME',
    'PASSWORD': 'YOUR-PASSWORD'
}

ACTIVEMQ = {
    "brokers": "127.0.1.1:61613",
    "amq_queues": ["/queue/ReductionPending"],
    "amq_user": "admin",
    "amq_pwd": "admin",
    "postprocess_error": "/queue/ReductionError",
    "reduction_started": "/queue/ReductionStarted",
    "reduction_complete": "/queue/ReductionComplete",
    "reduction_error": "/queue/ReductionError"
}

MYSQL = {
    'HOST': 'localhost',
    'USER': 'test-user',
    'PASSWD': 'pass',
    'DB': 'autoreduction',
    'PORT': '3306',
}

PATH_TO_FILE = os.path.dirname(os.path.realpath(__file__))
PATH_TO_TEST_OUTPUT = os.path.join(PATH_TO_FILE, 'test-output')

try:
    os.makedirs(PATH_TO_TEST_OUTPUT)
except OSError:
    # This should only ever fail if the path already exists
    pass

ARCHIVE_MONITOR_LOG = os.path.join(PATH_TO_TEST_OUTPUT, 'archive_monitor.log')

INST_PATH = os.path.join(PATH_TO_TEST_OUTPUT, 'data-archive', 'NDX{}', 'Instrument')

