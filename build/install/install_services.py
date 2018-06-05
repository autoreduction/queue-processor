"""
Python wraps to windows/linux install scripts for services
"""
import os
import subprocess

from build.install.settings import INSTALL_DIRS

PATH_TO_DIR = os.path.dirname(os.path.realpath(__file__))


def install_service(service_name):
    """
    Given a service name, find the correct install script, run it and return boolean for success
    :param service_name: The name of the service to install
    :return: True: exit code of installation script was 0
             False: exit code of installation script was non-zero
    """
    install_script = os.path.join(PATH_TO_DIR, (service_name + '.{}'))
    install_path = ''
    unzip_path = ''
    if os.name == 'nt':
        if service_name == 'mantid':
            # No need to install mantid on windows currently so skip this
            return True
        install_script = install_script.format('bat')
        install_path = INSTALL_DIRS[service_name]
        unzip_path = INSTALL_DIRS['7zip-location']
    else:
        install_script = install_script.format('sh')
    try:
        print("Installing %s with script %s" % (service_name, install_script))
        with open(os.path.join(PATH_TO_DIR, 'build.log'), 'w+') as logging:
            subprocess.check_call([install_script, install_path, unzip_path], stdout=logging)
    except subprocess.CalledProcessError:
        return False
    return True
