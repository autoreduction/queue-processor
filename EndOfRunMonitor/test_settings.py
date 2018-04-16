# ICAT
ICAT_SETTINGS = {
    'AUTH': 'YOUR-ICAT-AUTH-TYPE',
    'URL': 'YOUR-ICAT-WSDL-URL',
    'USER': 'YOUR-ICAT-USERNAME',
    'PASSWORD': 'YOUR-PASSWORD'
}
# ActiveMQ
ACTIVEMQ = {
    "brokers": "YOUR-ACTIVEMQ-URL:61613",
    "amq_queues": ["/queue/ReductionPending"],
    "amq_user": "YOUR-ACTIVEMQ-USERNAME",
    "amq_pwd": "YOUR-ACTIVEMQ-PASSWORD",
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

ARCHIVE_MONITOR_LOG = 'tests/archive_monitor.log'

INST_PATH = 'tests/data-archive'
