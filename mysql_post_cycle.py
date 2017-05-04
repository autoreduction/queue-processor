import mysql.connector

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