"""
Python wraps to windows/linux schema generation scripts for services
"""
import os
import subprocess

SUPER_USER_CREATE = ("from django.contrib.auth.models import User;" +
                     "User.objects.filter(username='super').delete();" +
                     "User.objects.create_superuser('super', '', 'super')")


def run_sql_file(sql_file_location):
    """
    Runs a sql file on the localhost database
    :param sql_file_location: file path to the sql file
    :return: True: exit code of script was 0
             False: exit code of script was non-zero
    """
    # Todo: need to fix the below and ensure database setup is functioning correctly
    # ToDo: deal with pipes?
    try:
        subprocess.check_call(['mysql < %s' % sql_file_location], shell=True)
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
        subprocess.check_call(['python', path_to_manage, 'migrate', 'auth'])
        subprocess.check_call(['python', path_to_manage, 'makemigrations', 'reduction_viewer'])
        subprocess.check_call(['python', path_to_manage, 'migrate', 'reduction_viewer'])
        echo_proc = subprocess.Popen(['echo', SUPER_USER_CREATE], shell=True, stdout=subprocess.PIPE)
        manage_proc = subprocess.Popen(['python', path_to_manage, 'shell'], stdin=echo_proc.stdout, stdout=subprocess.PIPE)
        echo_proc.stdout.close()
        manage_proc.communicate()
    except subprocess.CalledProcessError:
        return False
    return True
