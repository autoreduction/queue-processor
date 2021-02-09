# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Python wraps to windows/linux schema generation scripts for services
"""
from __future__ import print_function

import os
import sys

from build.utils.process_runner import run_process_and_log

PATH_TO_DIR = os.path.dirname(os.path.realpath(__file__))


def generate_schema(project_root_path, logger):
    """
    Call django migrations to create testing database schema
    :param project_root_path: The full path to the root directory of the project
    :param logger: log handler
    :return: True: exit code of script was 0
             False: exit code of script was non-zero
    """
    path_to_manage = os.path.join(project_root_path, 'WebApp', 'autoreduce_webapp', 'manage.py')
    for database in ['admin', 'sessions', 'auth', 'reduction_viewer', 'instrument']:
        logger.info("Migrating %s" % database)
        if run_process_and_log([sys.executable, path_to_manage, 'makemigrations', database]) is False:
            logger.error("Error encountered when makingmigrations for %s" % database)
            return False
        if run_process_and_log([sys.executable, path_to_manage, 'migrate', database]) is False:
            logger.error("Error encountered when migrating %s" % database)
            return False

    logger.info("Adding super user")
    # Custom manage.py command
    if run_process_and_log([sys.executable, path_to_manage, 'add_super']) is False:
        logger.error("Error encountered when adding super user")
        return False
    logger.info("Database migrated successfully")
    return True
