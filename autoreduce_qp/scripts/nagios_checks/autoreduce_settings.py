# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Settings for Nagios checks
"""
from requests.auth import HTTPBasicAuth

# ActiveMQ
ACTIVEMQ = {
    "host": "reducequeue",
    "queues": ["ReductionPending", "ReductionError"],
    "username": "YOUR-ACTIVEMQ-USERNAME",
    "password": "YOUR-ACTIVEMQ-PASSWORD",
    "api-path": ":8161/api/jolokia/read/org.apache.activemq:type=Broker,"
    "brokerName=localhost,destinationType=Queue"
}

MYSQL = {
    "host": "reducequeue",
    "username": "YOUR-MYSQL-USERNAME",
    "password": "YOUR-MYSQL-USERNAME",
    "db": "autoreduction"
}

ISIS_MOUNT = 'Z:\\'

ACTIVEMQ_URL = "http://" + ACTIVEMQ['host'] + ACTIVEMQ['api-path']
ACTIVEMQ_AUTH = HTTPBasicAuth(ACTIVEMQ['username'], ACTIVEMQ['password'])
