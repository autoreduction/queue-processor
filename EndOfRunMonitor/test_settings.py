"""
Settings for connecting to the test services that run locally
"""
import os

# ICAT
ICAT_SETTINGS = {
    'AUTH': 'YOUR-ICAT-AUTH-TYPE',
    'URL': 'YOUR-ICAT-WSDL-URL',
    'USER': 'YOUR-ICAT-USERNAME',
    'PASSWORD': 'YOUR-PASSWORD'
}
# ActiveMQ
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

# Reduction database
MYSQL = {
    'HOST': 'localhost',
    'USER': 'test-user',
    'PASSWD': 'pass',
    'DB': 'autoreduction',
    'PORT': '3306',
}

PATH_TO_FILE = os.path.dirname(os.path.realpath(__file__))

ARCHIVE_MONITOR_LOG = os.path.join(PATH_TO_FILE, 'tests', 'archive_monitor.log')

INST_PATH = os.path.join(PATH_TO_FILE, 'tests', 'data-archive')
