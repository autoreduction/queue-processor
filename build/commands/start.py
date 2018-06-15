"""
Command to start services running
"""
from __future__ import print_function

import os
import time

# pylint:disable=no-name-in-module,import-error
from distutils.core import Command

from build.utils.process_runner import run_process_and_log


class Start(Command):
    """
    Command to start the activeMQ service
    """

    description = 'Start the services that are required to test the project: ActiveMQ'
    user_options = []

    def initialize_options(self):
        """ Currently not required as we are only starting ActiveMQ
            If more services become required we will need to add parameters for this"""
        pass

    def finalize_options(self):
        """ See above comment regarding only ActiveMQ """
        pass

    # pylint:disable=no-self-use
    def run(self):
        """
        If activemq in expected install path, run `activemq start`
        """
        from build.settings import INSTALL_DIRS
        location = os.path.join(INSTALL_DIRS['activemq'],
                                'apache-activemq-5.15.3',
                                'bin', 'activemq')
        if os.path.isfile(location):
            run_process_and_log([location, 'start'])
            time.sleep(2)  # Ensure that activemq process has started before you continue
        else:
            print("Unable to start ActiveMQ service."
                  "Files not found at location %s" % location)
