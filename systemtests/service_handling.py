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
from subprocess import Popen


from build.test_settings import ACTIVEMQ_EXECUTABLE
from utils.project.structure import get_project_root


def start_activemq():
    """ Start the activemq process"""
    Popen(['sudo', ACTIVEMQ_EXECUTABLE, 'start'])
    time.sleep(3)


def stop_activemq():
    """ Stop the activemq process"""
    Popen(['sudo', ACTIVEMQ_EXECUTABLE, 'stop'])


def start_queue_processors():
    """ Start the Queue Processors"""
    queue_processor_dir = os.path.join(get_project_root(), 'QueueProcessors')
    Popen(['sudo', '{}/./restart.sh'.format(queue_processor_dir), sys.executable])
    time.sleep(3)


def stop_queue_processors():
    """ Stop the Queue Processors"""
    queue_processor_dir = os.path.join(get_project_root(), 'QueueProcessors')
    Popen(['sudo', '{}/./stop.sh'.format(queue_processor_dir), sys.executable])
