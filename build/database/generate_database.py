"""
Python wraps to windows/linux schema generation scripts for services
"""
import os
import subprocess


def run_sql_file(sql_file_location):
    """
    Runs a sql file on the localhost database
    :param sql_file_location: file path to the sql file
    :return: True: exit code of script was 0
             False: exit code of script was non-zero
    """
    try:
        with open(sql_file_location, 'r') as input_file:
            subprocess.check_call(['mysql', '-uroot'],
                                  stdin=input_file, shell=True,
                                  stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        return False
    return True


def generate_schema(project_root_path):
    """
    Call django migrations to create testing database schema
    :param project_root_path: The full path to the root directory of the project
    :return: True: exit code of script was 0
             False: exit code of script was non-zero
    """
    path_to_manage = os.path.join(project_root_path, 'WebApp', 'autoreduce_webapp', 'manage.py')
    try:
        for database in ['admin', 'sessions', 'auth', 'reduction_viewer']:
            subprocess.check_call(['python', path_to_manage, 'makemigrations', database])
            subprocess.check_call(['python', path_to_manage, 'migrate', database])
        subprocess.check_call(['python', path_to_manage, 'add_super'])  # Custom manage.py command to add super user
    except subprocess.CalledProcessError:
        return False
    return True
