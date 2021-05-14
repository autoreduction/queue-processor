# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Command to move test_settings.py to settings.py
"""
import os
from shutil import copyfile

# pylint:disable=no-name-in-module
from distutils.core import Command

from build.utils.common import BUILD_LOGGER, ROOT_DIR


class MigrateTestSettings(Command):
    """
    Class to copy test_credentials.ini to credentials.ini
    """

    description = 'Overwrite the credentials.py files with test_credentials.py'
    user_options = []

    def initialize_options(self):
        # This function needs to be overriden for a class inheriting the distutils.utils.Command
        # even if it is left empty, otherwise a RuntimeError is thrown whenever the
        # command is called from setup.py
        pass

    def finalize_options(self):
        # pylint:disable=attribute-defined-outside-init
        self.utils_path = os.path.join(ROOT_DIR, 'utils')

    def run(self):
        """ Copy all test files from the test files list to desired locations """
        BUILD_LOGGER.print_and_log("================== Migrate credentials ====================")
        self._migrate_test_settings(self.utils_path)
        BUILD_LOGGER.print_and_log("Credentials successfully migrated\n")

    @staticmethod
    def _migrate_test_settings(utils_path):
        try:
            test_credentials_path = os.path.join(utils_path, 'test_credentials.ini')
            credentials_path = os.path.join(utils_path, 'credentials.ini')
            copyfile(test_credentials_path, credentials_path)
        except OSError as error:
            BUILD_LOGGER.logger.error(error)
            raise
