import os
from distutils.core import Command

from build.database.generate_database import run_sql_file, generate_schema
from build.utils.common import BUILD_LOGGER, ROOT_DIR


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
        if run_sql_file(self.setup_sql_path, BUILD_LOGGER.logger) is False:
            return
        BUILD_LOGGER.print_and_log("Migrating databases from django model")
        if generate_schema(ROOT_DIR, BUILD_LOGGER.logger) is False:
            return
        BUILD_LOGGER.print_and_log("Populating database with test data")
        if run_sql_file(self.populate_sql_path, BUILD_LOGGER.logger) is False:
            return
        BUILD_LOGGER.print_and_log("Test database successfully initialised\n")
