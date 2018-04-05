#! /usr/bin/env python
"""
Check the number of consumer for the list is atleast 1
"""
from __future__ import print_function
import sys

import requests
from requests.auth import HTTPBasicAuth

# pylint: disable=import-error
from Scripts.NagiosChecks.autoreduce_settings import ACTIVEMQ


ACTIVEMQ_URL = "http://" + ACTIVEMQ['host'] + ACTIVEMQ['api-path']
ACTIVEMQ_AUTH = HTTPBasicAuth(ACTIVEMQ['username'], ACTIVEMQ['password'])


# pylint: disable=invalid-name
def checkConsumer():
    """
    checks that the consumers are consuming from queues correctly
    :return: 0 - Success
             2 - Failure
    """
    for queue in ACTIVEMQ['queues']:
        r = requests.get(ACTIVEMQ_URL + ",destinationName=" + queue + "/ConsumerCount",
                         auth=ACTIVEMQ_AUTH)

        consumer_count = r.json()['value']
        # print(queue + " consumerCount = " + str(r.json()['value']))

        if consumer_count < 1:
            print("No consumers for  " + str(queue))
            return 2
    return 0


# pylint: disable=using-constant-test
if "__name__":
    sys.exit(checkConsumer())
