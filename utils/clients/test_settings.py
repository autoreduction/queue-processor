"""
Settings for connecting to the test services that run locally
"""

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
