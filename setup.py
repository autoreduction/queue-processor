import os
from shutil import copyfile

from distutils.core import Command
from setuptools import setup

from build.install.install_services import install_service
from build.tests.validate_installs import validate_installs
from utils.clients.database_client import DatabaseClient


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))


class MigrateTestSettings(Command):
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
        self._migrate_test_settings(self.test_settings_paths)

    @staticmethod
    def _migrate_test_settings(all_paths):
        for path_to_dir in all_paths:
            test_settings_path = os.path.join(path_to_dir, 'test_settings.py')
            settings_path = os.path.join(path_to_dir, 'settings.py')
            copyfile(test_settings_path, settings_path)


class InitialiseTestDatabase(Command):
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
        db_client = DatabaseClient()
        self._read_sql_and_execute(self.setup_sql_path, db_client)
        # generate testing database schema
        self._read_sql_and_execute(self.populate_sql_path, db_client)

    @staticmethod
    def _read_sql_and_execute(sql_file_path, db_client):
        with open(sql_file_path, 'r') as sql_file:
            query = "".join(sql_file.readlines())
        db_client.execute_query(query)


class InstallExternals(Command):
    description = 'Install external dependencies of the project'
    user_options = [('services=', 's', 'comma separated list of services to install')]

    def initialize_options(self):
        self.services = None

    def finalize_options(self):
        self.services = ['activemq', 'icat', 'mantid'] \
            if self.services is None else self.services

    def run(self):
        # Validate
        valid = self._validate_services(self.services)
        for service in valid:
            if valid[service] is False:
                install_service(service)
        # re-validate
        _ = self._validate_services(self.services, quiet=False)

    @staticmethod
    def _validate_services(list_of_services, quiet=True):
        """
        Check if services are installed and usable. Current checks:
            ActiveMQ, icat, Mantid
        :param quiet: boolean to decide if anything is printed on validation failure
        :return: dictionary of {"service_name": validity(True/False)}
        """
        service_validity = validate_installs(list_of_services)
        if quiet is False:
            for service in service_validity:
                if service_validity[service] is False:
                    print("Unable to validate %s install" % service)
        return service_validity


setup(name='AutoReduction',
      version='1.0',
      description='ISIS AutoReduction service',
      author='ISIS Autoreduction Team',
      url='https://github.com/ISISScientificComputing/autoreduce/',
      install_requires=[
          'Django==1.11.12',
          'django_extensions==2.0.7',
          'django-user-agents==0.3.2',
          'MySQL-python==1.2.5',
          'python-daemon==2.1.2',
          'requests==2.18.4',
          'SQLAlchemy==1.2.7',
          'stomp.py==4.1.20',
          'suds==0.4',
          'Twisted==14.0.2',
          'watchdog==0.8.3'
      ],
      cmdclass={
          'migrate_test_settings': MigrateTestSettings,
          'initialise_test_database': InitialiseTestDatabase,
          'install_externals': InstallExternals,
      },
      )
