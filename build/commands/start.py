"""
Command to start services running
"""
import os

from distutils.core import Command

from build.utils.process_runner import run_process_and_log


class Start(Command):

    description = 'Create the test database on local host'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from build.settings import INSTALL_DIRS
        location = os.path.join(INSTALL_DIRS['activemq'], 'apache-activemq-5.15.3', 'bin', 'activemq')
        if os.path.isfile(location):
            run_process_and_log([location, 'start'])
        else:
            print("Unable to start ActiveMQ service. Files not found at location %s" % location)
