"""
Script for resetting the database by hand at the end of each cycle
"""
from __future__ import print_function

import sys
import os
from shutil import copyfile
# pylint: disable=import-error
import mysql.connector

# Directory of the folder with all of the database backups in
BACKUP_DIRECTORY = 'C:\\database_backup\\'

# Get the latest cycle from the arguments given
try:
    LATEST_CYCLE = sys.argv[1]
except IndexError as exp:
    print('Please enter the name of the latest cycle (e.g. cycle_16_5)')
    sys.exit(0)

NEW_CYCLE_DIRECTORY = BACKUP_DIRECTORY + LATEST_CYCLE

# Make the directory if it doesn't exist
if not os.path.exists(NEW_CYCLE_DIRECTORY):
    os.makedirs(NEW_CYCLE_DIRECTORY)

# Copy all of the files in
for backup_files in os.listdir(BACKUP_DIRECTORY):
    if backup_files.endswith('.sql'):
        file_path = BACKUP_DIRECTORY + backup_files
        copyfile(file_path, NEW_CYCLE_DIRECTORY + '\\' + backup_files)

# Login to the database
CONNECTION = mysql.connector.connect(user='root', password='activedev',
                                     host='reducedev2', database='autoreduction')
CURSOR = CONNECTION.cursor()

# The list of tables to be deleted
TABLES_TO_DELETE = ['reduction_viewer_status', 'reduction_viewer_setting',
                    'reduction_viewer_reductionrun', 'reduction_viewer_reductionlocation',
                    'reduction_viewer_notification', 'reduction_variables_instrumentvariable',
                    'reduction_viewer_experiment', 'reduction_viewer_datalocation',
                    'reduction_variables_variable', 'reduction_variables_runvariable']

# Turn off foreign key checks and safe updating momentarily
CURSOR.execute("SET FOREIGN_KEY_CHECKS = 0")
CURSOR.execute("SET SQL_SAFE_UPDATES = 0")

# Loop through each table and delete all of the entries
for table in TABLES_TO_DELETE:
    print('Deleting all from ' + table)
    CURSOR.execute("DELETE FROM autoreduction." + table)

# Turn foreign key checks and safe updating
CURSOR.execute("SET FOREIGN_KEY_CHECKS = 1")
CURSOR.execute("SET SQL_SAFE_UPDATES = 1")

# Commit our changes
CONNECTION.commit()
