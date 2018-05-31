import os
from shutil import copyfile
from setuptools import setup
from setuptools.command.develop import develop

from utils.clients.database_client import DatabaseClient


class CustomDevelopCommand(develop):
    def run(self):
        develop.run(self)
        root_dir = os.path.dirname(os.path.realpath(__file__))
        # ============================== Migrate test settings =============================== #
        test_settings_paths = [os.path.join(root_dir, 'Scripts', 'ActiveMQTests'),
                               os.path.join(root_dir, 'utils'),
                               os.path.join(root_dir, 'WebApp', 'autoreduce_webapp', 'autoreduce_webapp')]
        self._migrate_test_settings(test_settings_paths)

        # =============================== Initialise database ================================ #
        db_client = DatabaseClient()
        database_build_dir = os.path.join(root_dir, 'Scripts', 'Build', 'database')
        setup_sql_path = os.path.join(database_build_dir, 'test_db_setup.sql')
        self._read_sql_and_execute(setup_sql_path, db_client)
        # generate testing database schema
        populate_sql_path = os.path.join(database_build_dir, 'populate_reduction_viewer.sql')
        self._read_sql_and_execute(populate_sql_path, db_client)

        # =============================== Install externals ================================== #
        # Run installs
        # Validate externals

    @staticmethod
    def _migrate_test_settings(all_paths):
        for path_to_dir in all_paths:
            test_settings_path = os.path.join(path_to_dir, 'test_settings.py')
            settings_path = os.path.join(path_to_dir, 'settings.py')
            copyfile(test_settings_path, settings_path)

    @staticmethod
    def _read_sql_and_execute(sql_file_path, db_client):
        with open(sql_file_path, 'r') as sql_file:
            query = "".join(sql_file.readlines())
        db_client.execute_query(query)


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
          'develop': CustomDevelopCommand,
      },
      )
