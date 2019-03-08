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

import os
from subprocess import Popen


from build.test_settings import ACTIVEMQ_EXECUTABLE
from utils.project.structure import get_project_root


def _start_activemq():
    """ Start the activemq process"""
    Popen([ACTIVEMQ_EXECUTABLE, 'start'])


def _stop_activemq():
    """ Stop the activemq process"""
    Popen([ACTIVEMQ_EXECUTABLE, 'stop'])


def _start_queue_processors():
    """ Start the Queue Processors"""
    queue_processor_dir = os.path.join(get_project_root(), 'QueueProcessors')
    Popen(['{}/./restart.sh'.format(queue_processor_dir)])


def _stop_queue_processors():
    """ Stop the Queue Processors"""
    queue_processor_dir = os.path.join(get_project_root(), 'QueueProcessors')
    Popen(['{}/./stop.sh'.format(queue_processor_dir)])
