"""
Command to move test_settings.py to settings.py
"""
import os
from shutil import copyfile

# pylint:disable=no-name-in-module,import-error
from distutils.core import Command

from build.utils.common import BUILD_LOGGER, ROOT_DIR


class MigrateTestSettings(Command):
    """
    Class to copy all test_settings.py files listed to settings.py
    """

    description = 'Overwrite the settings.py files with test_settings.py'
    user_options = []

    def initialize_options(self):
        """ Initialise empty list """
        # pylint:disable=attribute-defined-outside-init
        self.test_settings_paths = []

    def finalize_options(self):
        """ Add known test_settings.py files to list """
        # pylint:disable=attribute-defined-outside-init
        self.test_settings_paths = [os.path.join(ROOT_DIR, 'build'),
                                    os.path.join(ROOT_DIR, 'Scripts', 'ActiveMQTests'),
                                    os.path.join(ROOT_DIR, 'utils'),
                                    os.path.join(ROOT_DIR, 'WebApp', 'autoreduce_webapp',
                                                 'autoreduce_webapp')]

    def run(self):
        """ Copy all test files from the test files list to desired locations """
        BUILD_LOGGER.print_and_log("================== Migrate test settings ====================")
        self._migrate_test_settings(self.test_settings_paths)
        BUILD_LOGGER.print_and_log("Test settings successfully migrated\n")

    @staticmethod
    def _migrate_test_settings(all_paths):
        """
        Copy any test_settings.py files in given directory list to settings.py files
        :param all_paths: All directories containing test_settings.py
        """
        try:
            for path_to_dir in all_paths:
                test_settings_path = os.path.join(path_to_dir, 'test_settings.py')
                settings_path = os.path.join(path_to_dir, 'settings.py')
                copyfile(test_settings_path, settings_path)
        except OSError as error:
            BUILD_LOGGER.logger.error(error)
            raise
