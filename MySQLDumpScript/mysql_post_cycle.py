import mysql.connector
import sys, os
from shutil import copyfile

# Directory of the folder with all of the database backups in
BACKUP_DIRECTORY = 'C:\\database_backup\\'

# Get the latest cycle from the arguments given
try:
	latest_cycle = sys.argv[1]
except IndexError as e:
	print 'Please enter the name of the latest cycle (e.g. cycle_16_5)'
	sys.exit(0)

NEW_CYCLE_DIRECTORY = BACKUP_DIRECTORY + latest_cycle

# Make the directory if it doesn't exist
if not os.path.exists(NEW_CYCLE_DIRECTORY):
	os.makedirs(NEW_CYCLE_DIRECTORY)

# Copy all of the files in 
for file in os.listdir(BACKUP_DIRECTORY):
	if file.endswith('.sql'):
		file_path = BACKUP_DIRECTORY + file
		copyfile(file_path, NEW_CYCLE_DIRECTORY + '\\' + file)
		
# Login to the database
connection = mysql.connector.connect(user='root', password='activedev', 
									 host='reducedev2', database='autoreduction')
cursor = connection.cursor()

# The list of tables to be deleted
tables_to_delete = ['reduction_viewer_status', 'reduction_viewer_setting',
					'reduction_viewer_reductionrun','reduction_viewer_reductionlocation', 
					'reduction_viewer_notification','reduction_variables_instrumentvariable',
					'reduction_viewer_experiment','reduction_viewer_datalocation',
					'reduction_variables_variable','reduction_variables_runvariable']

# Turn off foreign key checks and safe updating momentarily
cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
cursor.execute("SET SQL_SAFE_UPDATES = 0")

# Loop through each table and delete all of the entries
for table in tables_to_delete:
	print 'Deleting all from ' + table
	cursor.execute("DELETE FROM autoreduction." + table)

# Turn foreign key checks and safe updating
cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
cursor.execute("SET SQL_SAFE_UPDATES = 1")

# Commit our changes
connection.commit()