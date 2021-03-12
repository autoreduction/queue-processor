# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Command to start services running
"""
from __future__ import print_function

import os
import time

# pylint:disable=no-name-in-module
from distutils.core import Command

from build.utils.process_runner import run_process_and_log, run_process_with_shell


class Start(Command):
    """
    Command to start the activeMQ service
    """

    description = 'Start the services that are required to test the project: ActiveMQ'
    user_options = []

    def initialize_options(self):
        """ Currently not required as we are only starting ActiveMQ
            If more services become required we will need to add parameters for this"""

    def finalize_options(self):
        """ See above comment regarding only ActiveMQ """

    def run(self):
        """
        If activemq in expected install path, run `activemq start`
        """
        # pylint:disable=import-outside-toplevel
        from build.settings import ACTIVEMQ_EXECUTABLE
        location = ACTIVEMQ_EXECUTABLE
        if os.name == 'nt':
            location = location + '.bat'
            start_new_terminal = ['start', 'cmd', '/c']
            if self._check_valid_path(location):
                run_process_with_shell(start_new_terminal + [location, 'start'])
                time.sleep(2)  # Ensure that activemq process has started before you continue
        else:
            if self._check_valid_path(location):
                if run_process_and_log([location, 'start']):
                    time.sleep(2)  # Ensure that activemq process has started before you continue
                else:
                    print("Unable to start ActiveMQ service." " Please see build.log for details.")

    @staticmethod
    def _check_valid_path(path):
        if os.path.isfile(path):
            return True
        print("Unable to start ActiveMQ service." "Files not found at location %s" % path)
        return False
