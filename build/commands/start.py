"""
Command to start services running
"""
from __future__ import print_function

import os
import time

# pylint:disable=no-name-in-module,import-error
from distutils.core import Command

from build.utils.common import validate_user_input
from build.utils.process_runner import run_process_and_log, run_process_with_shell
from utils.project.structure import get_project_root


class Start(Command):
    """
    Command to start the activeMQ service
    """

    description = 'Start the services that are required to test the project: ActiveMQ, QueueProcessors'
    user_options = [('services=', 's', 'comma separated list of services to start')]

    def initialize_options(self):
        """ Init service list"""
        # pylint:disable=attribute-defined-outside-init
        self.services = []

    def finalize_options(self):
        """ split and transform to lower case user input if provided """
        # pylint:disable=attribute-defined-outside-init
        if self.services:
            self.services = self.services.split(",")
            self.services = [service.lower() for service in self.services]
        else:
            self.services = ['activemq', 'queues']

    def run(self):
        """
        If activemq in expected install path, run `activemq start`
        """
        validate_user_input(self.services, ['activemq', 'queues'])
        if 'activemq' in self.services:
            self.start_activemq()
        if 'queues' in self.services:
            self.start_queues()

    def start_activemq(self):
        """ start the activemq process on local machine """
        from build.settings import ACTIVEMQ_EXECUTABLE
        location = ACTIVEMQ_EXECUTABLE
        if os.name == 'nt':
            location += '.bat'
            start_new_terminal = ['start', 'cmd', '/c']
            if self._check_valid_path(location):
                run_process_with_shell(start_new_terminal + [location, 'start'])
                time.sleep(2)  # Ensure that activemq process has started before you continue
        else:
            if self._check_valid_path(location):
                run_process_and_log([location, 'start'])
                time.sleep(2)  # Ensure that activemq process has started before you continue

    @staticmethod
    def start_queues():
        """ Start the queue processors"""
        if os.name == 'nt':
            print("Unable to start QueueProcessors on windows")
        else:
            script = os.path.join(get_project_root(), 'QueueProcessors', 'restart.sh')
            if run_process_and_log([script]) is False:
                print("Unable to start QueueProcessor services. "
                      "Script: \'{}\' failed".format(script))

    @staticmethod
    def _check_valid_path(path):
        if os.path.isfile(path):
            return True
        print("Unable to start ActiveMQ service. "
              "Files not found at location %s" % path)
        return False
