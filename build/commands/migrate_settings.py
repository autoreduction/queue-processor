"""
Command to move test_settings.py to settings.py
"""
import os
from shutil import copyfile

# pylint:disable=no-name-in-module,import-error
from distutils.core import Command

from build.utils.common import build_logger
from utils.project.structure import get_project_root


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
        root = get_project_root()
        self.test_settings_paths = [os.path.join(root, 'build'),
                                    os.path.join(root, 'scripts', 'activemq_tests'),
                                    os.path.join(root, 'utils'),
                                    os.path.join(root, 'WebApp', 'autoreduce_webapp',
                                                 'autoreduce_webapp'),
                                    os.path.join(root, 'QueueProcessors',
                                                 'AutoreductionProcessor'),
                                    os.path.join(root, 'QueueProcessors',
                                                 'QueueProcessor')]

    def run(self):
        """ Copy all test files from the test files list to desired locations """
        build_logger().print_and_log("================== Migrate test settings ====================")
        self._migrate_test_settings(self.test_settings_paths)
        build_logger().print_and_log("Test settings successfully migrated\n")

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
            build_logger().logger.error(error)
            raise
