# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module to generate a testing database to be used for local testing of the project
"""
import os
# pylint:disable=no-name-in-module,import-error
from distutils.core import Command

from build.database.generate_database import add_test_user, run_sql_file, generate_schema
from build.utils.common import BUILD_LOGGER, ROOT_DIR


class InitialiseTestDatabase(Command):
    """
    Command to initialise the local host database and populate it with dummy data
    """
    description = 'Create the test database on local host'
    user_options = []

    def initialize_options(self):
        """ Initialise path variables """
        # pylint:disable=attribute-defined-outside-init
        self.setup_sql_path = None
        self.populate_sql_path = None

    def finalize_options(self):
        """ Generate paths to sql scripts """
        database_build_dir = os.path.join(ROOT_DIR, 'build', 'database')
        # pylint:disable=attribute-defined-outside-init
        self.setup_sql_path = os.path.join(database_build_dir, 'test_db_setup.sql')
        self.populate_sql_path = os.path.join(database_build_dir, 'populate_reduction_viewer.sql')

    def run(self):
        """ Run the setup scripts required for localhost database """
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
        BUILD_LOGGER.print_and_log("Adding test user from settings")
        if add_test_user(BUILD_LOGGER.logger) is False:
            return
        BUILD_LOGGER.print_and_log("Test database successfully initialised\n")
