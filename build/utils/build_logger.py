"""
Class to handle logging for build script
"""

import os
import logging


class BuildLogger(object):

    logger = None

    def __init__(self, root_directory):
        # Clear log file
        with open(os.path.join(root_directory, 'build.log'), 'w'):
            pass
        self._initialise_logger(root_directory)

    def _initialise_logger(self, root_directory):
        self.logger = logging.getLogger("build")
        handler = logging.FileHandler(os.path.join(root_directory, 'build.log'))
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s : %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def print_and_log(self, message, log_level=logging.INFO):
        self.logger.log(level=log_level, msg=message)
        print(message)
