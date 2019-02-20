## Database Management

This script should be used with **WITH CAUTION!**. The script has the ability to wipe the production 
database so think carefully while using it.

### Setup
Ensure that `utils/settings.py` is using the correct credentials for the task you want to perform.

### Use
The script will not allow you to wipe the database without a backup file being present so first a
backup must be created. To do this run the following:
```
$ python reset_database_post_cycle.py
```
Then when prompted enter the following details:
```
'Backup' or 'Wipe': Backup
Current cycle name: cycle_xx_y  # Where xx is the current year and y is the cycle iteration e.g. cycle_18_1
Database user name: root        # This could be something else depending on your local settings
Database password (leave blank if none):      # Type database password here
```
After this, a database .sql backup file will be made and added to 
`C:\database_backup\cycle_xx_y\cycle_xx_y.sql`

After performing a backup, to wip a database perform the above steps but use the keyword 'Wipe'
 as the input to the first question.