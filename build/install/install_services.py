"""
Python wraps to windows/linux install scripts for services
"""
import os
import subprocess

PATH_TO_DIR = os.path.dirname(os.path.realpath(__file__))


def install_service(service_name):
    """
    Given a service name, find the correct install script, run it and return boolean for success
    :param service_name: The name of the service to install
    :return: True: exit code of installation script was 0
             False: exit code of installation script was non-zero
    """
    install_script = os.path.join(PATH_TO_DIR, service_name, '.%s')
    if os.name == 'nt':
        install_script % 'bat'
    else:
        install_script % 'sh'
    try:
        subprocess.check_call([install_script])
    except subprocess.CalledProcessError:
        return False
    return True
