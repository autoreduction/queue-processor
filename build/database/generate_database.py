"""
Python wraps to windows/linux schema generation scripts for services
"""
import os
import subprocess

from build.utils.process_runner import run_process_and_log

PATH_TO_DIR = os.path.dirname(os.path.realpath(__file__))


def run_sql_file(sql_file_location, logger):
    """
    Runs a sql file on the localhost database
    :param sql_file_location: file path to the sql file
    :param logger: log handler
    :return: True: exit code of script was 0
             False: exit code of script was non-zero
    """
    try:
        print("Running script: %s" % sql_file_location)
        with open(sql_file_location, 'r') as input_file:
            mysql_process = subprocess.Popen(['mysql', '-uroot'],
                                             stdin=input_file, shell=True,
                                             stderr=subprocess.PIPE,
                                             stdout=subprocess.PIPE)
            process_output, _ = mysql_process.communicate()
            if process_output:
                print(process_output)
    except subprocess.CalledProcessError:
        print("Script did not complete. Check build.log for more details.")
        return False
    print("Script ran successfully")
    return True


def generate_schema(project_root_path, logger):
    """
    Call django migrations to create testing database schema
    :param project_root_path: The full path to the root directory of the project
    :param logger: log handler
    :return: True: exit code of script was 0
             False: exit code of script was non-zero
    """
    path_to_manage = os.path.join(project_root_path, 'WebApp', 'autoreduce_webapp', 'manage.py')
    try:
        for database in ['admin', 'sessions', 'auth', 'reduction_viewer']:
            print("Migrating %s" % database)
            run_process_and_log(['python', path_to_manage, 'makemigrations', database], logger)
            run_process_and_log(['python', path_to_manage, 'migrate', database], logger)

        print("Adding super user")
        run_process_and_log(['python', path_to_manage, 'add_super'], logger)  # Custom manage.py command
    except subprocess.CalledProcessError:
        print("Error encountered when migrating database. "
                     "Check build.log for more details.")
        return False
    print("Database migrated successfully")
    return True
