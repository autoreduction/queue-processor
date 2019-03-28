# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
"""
Functions to handle start/stop of external services such as activemq and queue processors
"""

import sys
import os
import time
from subprocess import Popen, check_output, CalledProcessError

from utils.project.structure import get_project_root


def _check_root():
    """
    Raise exception if user is not root
    """
    system_test_dir = os.path.join(get_project_root(), 'systemtests')
    try:
        check_output(['{}/./check_root.sh'.format(system_test_dir)])
    except CalledProcessError:
        raise RuntimeError('User must be root to perform these operations')


def start_queue_processors():
    """ Start the Queue Processors"""
    _check_root()
    queue_processor_dir = os.path.join(get_project_root(), 'QueueProcessors')
    Popen(['sudo', '{}/./restart.sh'.format(queue_processor_dir), sys.executable])
    time.sleep(3)


def stop_queue_processors():
    """ Stop the Queue Processors"""
    _check_root()
    queue_processor_dir = os.path.join(get_project_root(), 'QueueProcessors')
    Popen(['sudo', '{}/./stop.sh'.format(queue_processor_dir), sys.executable])
    time.sleep(3)
