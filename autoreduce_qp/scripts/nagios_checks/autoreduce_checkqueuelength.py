# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# ! /usr/bin/env python
"""
Check the length of the queues
"""
# pylint: disable=duplicate-code
from __future__ import print_function
import sys

import requests

# pylint: disable=import-error
from autoreduce_qp.scripts.nagios_checks.autoreduce_settings import ACTIVEMQ, ACTIVEMQ_URL, ACTIVEMQ_AUTH


# pylint: disable=invalid-name
def checkQueueLength(warning, critical):
    """
    Ensures that the queue length is as expected
    :param warning: value to start reporting system warning
    :param critical: value to start reporting system critical
    :return: 0 - Success
             1 - Warning
             2 - Critical
    """
    for queue in ACTIVEMQ['queues']:
        r = requests.get(ACTIVEMQ_URL + ",destinationName=" + queue + "/QueueSize", auth=ACTIVEMQ_AUTH)

        queue_length = r.json()['value']
        # print(queue + " length = " + str(queue_length))

        if queue_length > warning:
            print(queue + " queue getting big " + str(queue_length))
            return 1
        if queue_length > critical:
            print(queue + " queue length is critical " + str(queue_length))
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(checkQueueLength(3, 10))
