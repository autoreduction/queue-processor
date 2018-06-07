"""
Contains all the setup.py commands
"""
import logging
import os

from distutils.core import Command
from shutil import copyfile

from build.database.generate_database import run_sql_file, generate_schema
from build.utils.build_logger import BuildLogger

# The root directory for the project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
BUILD_LOGGER = BuildLogger(ROOT_DIR)


class MigrateTestSettings(Command):
    """
    Command to move test_settings.py to settings.py
    """
    description = 'Overwrite the settings.py files with test_settings.py'
    user_options = []

    def initialize_options(self):
        self.test_settings_paths = []

    def finalize_options(self):
        self.test_settings_paths = [os.path.join(ROOT_DIR, 'build', 'install'),
                                    os.path.join(ROOT_DIR, 'Scripts', 'ActiveMQTests'),
                                    os.path.join(ROOT_DIR, 'utils'),
                                    os.path.join(ROOT_DIR, 'WebApp', 'autoreduce_webapp',
                                                 'autoreduce_webapp')]

    def run(self):
        BUILD_LOGGER.print_and_log("================== Migrate test settings ====================")
        self._migrate_test_settings(self.test_settings_paths)
        BUILD_LOGGER.print_and_log("Test settings successfully migrated\n")

    @staticmethod
    def _migrate_test_settings(all_paths):
        try:
            for path_to_dir in all_paths:
                test_settings_path = os.path.join(path_to_dir, 'test_settings.py')
                settings_path = os.path.join(path_to_dir, 'settings.py')
                copyfile(test_settings_path, settings_path)
        except OSError as error:
            BUILD_LOGGER.logger.error(error)
            raise


# =============================================================================================== #
# =============================================================================================== #
# =============================================================================================== #


class Help(Command):
    """
    Command to print the help information for setup.py
    """
    description = "Provide help on using this setup"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        help_text = (('Usage       :', 'python setup.py [commands]'),
                     ('Description :', 'A script designed to setup project and testing environment'),
                     ('', ''),
                     ('Commands: ', '')
                     )
        commands = (('     test_settings', 'Copy test_settings.py to settings.py'),
                    ('     database', 'Initialise database on localhost'),
                    ('     externals', 'Install all external programs'),
                    ('     help', 'Show the help documentation')
                    )
        for args in help_text:
            print '{0:<15} {1:<10}'.format(*args)
        for command in commands:
            print '{0:<20} {1:<10}'.format(*command)


# =============================================================================================== #
# =============================================================================================== #
# =============================================================================================== #


class InstallExternals(Command):
    """
    Command to install all the external requirements for the project
    """
    description = 'Install external dependencies of the project'
    user_options = [('services=', 's', 'comma separated list of services to install')]

    def initialize_options(self):
        self.services = ""

    def finalize_options(self):
        if self.services:
            self.services = self.services.split(",")
            self.services = [service.lower() for service in self.services]
        else:
            self.services = ['activemq', 'icat', 'mantid']
        if os.name == 'nt' and '7zip' not in self.services:
            self.services.append('7zip')

    def run(self):
        #  import here as this will fail if migrate test settings not performed
        from build.install.install_services import install_service

        BUILD_LOGGER.print_and_log("======== Installing external dependencies Database ==========")
        BUILD_LOGGER.print_and_log("Discovering already installed services")
        valid = self._validate_services(self.services)
        # Ensure 7zip is installed first
        if '7zip' in valid.keys():
            if valid['7zip'] is False:
                BUILD_LOGGER.print_and_log("Installing 7zip (required for other installations")
                install_service('7zip', BUILD_LOGGER.logger)
                # Remove to ensure it is not reinstalled
                del valid['7zip']
                BUILD_LOGGER.print_and_log("Installing other required services - this could take a few minutes")
        for service in valid:
            if valid[service] is False:
                install_service(service, BUILD_LOGGER.logger)
                BUILD_LOGGER.print_and_log("Running validation check to insure successful installation")
        valid = self._validate_services(self.services, quiet=False)
        if False in valid.values():
            raise RuntimeError("One or more services did not correctly install: \n"
                               "%s\n"
                               "See build.log for more details.")

    def _validate_services(self, list_of_services, quiet=True):
        """
        Check if services are installed and usable. Current checks:
            7Zip, ActiveMQ, icat, Mantid
        :param quiet: boolean to decide if anything is printed on validation failure
        :return: dictionary of {"service_name": validity(True/False)}
        """
        from build.tests.validate_installs import validate_installs
        service_validity = validate_installs(list_of_services)
        if quiet is False:
            for service in service_validity:
                if service_validity[service] is False:
                    BUILD_LOGGER.print_and_log("%s install did not validate" % service, logging.ERROR)
                else:
                    if service == 'mantid' and os.name == 'nt':
                        BUILD_LOGGER.print_and_log("Skipped mantid installation: "
                                                  "currently not required on windows", logging.WARNING)
                    else:
                        BUILD_LOGGER.print_and_log("%s is installed and validated" % service)
        return service_validity


# =============================================================================================== #
# =============================================================================================== #
# =============================================================================================== #


class InitialiseTestDatabase(Command):
    """
    Command to initialise the local host database and populate it with dummy data
    """
    description = 'Create the test database on local host'
    user_options = []

    def initialize_options(self):
        self.setup_sql_path = None
        self.populate_sql_path = None

    def finalize_options(self):
        database_build_dir = os.path.join(ROOT_DIR, 'build', 'database')
        self.setup_sql_path = os.path.join(database_build_dir, 'test_db_setup.sql')
        self.populate_sql_path = os.path.join(database_build_dir, 'populate_reduction_viewer.sql')

    def run(self):
        BUILD_LOGGER.print_and_log("==================== Building Database ======================")
        BUILD_LOGGER.print_and_log("Setting up database on local host")
        run_sql_file(self.setup_sql_path, BUILD_LOGGER.logger)
        BUILD_LOGGER.print_and_log("Migrating databases from django model")
        generate_schema(ROOT_DIR, BUILD_LOGGER.logger)
        BUILD_LOGGER.print_and_log("Populating database with test data")
        run_sql_file(self.populate_sql_path, BUILD_LOGGER.logger)
        BUILD_LOGGER.print_and_log("Test database successfully initialised\n")
