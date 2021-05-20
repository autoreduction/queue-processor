# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
#! /usr/bin/env python
"""
Check the number of consumer for the list is atleast 1
"""
from __future__ import print_function
import sys

import requests

# pylint: disable=import-error
from autoreduce_qp.scripts.nagios_checks.autoreduce_settings import ACTIVEMQ, ACTIVEMQ_URL, ACTIVEMQ_AUTH


# pylint: disable=invalid-name
def checkConsumer():
    """
    checks that the consumers are consuming from queues correctly
    :return: 0 - Success
             2 - Failure
    """
    for queue in ACTIVEMQ['queues']:
        r = requests.get(ACTIVEMQ_URL + ",destinationName=" + queue + "/ConsumerCount", auth=ACTIVEMQ_AUTH)

        consumer_count = r.json()['value']
        # print(queue + " consumerCount = " + str(r.json()['value']))

        if consumer_count < 1:
            print("No consumers for  " + str(queue))
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(checkConsumer())
