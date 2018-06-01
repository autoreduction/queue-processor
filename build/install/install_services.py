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
    args = ''
    if os.name == 'nt':
        if service_name == 'mantid':
            # No need to install mantid on windows currently so skip this
            return True
        install_script = install_script.format('bat')
        args = INSTALL_DIRS[service_name]
    else:
        install_script = install_script.format('sh')
    try:
        print("Installing %s with script %s" % (service_name, install_script))
        subprocess.check_call([install_script, args])
        print("Installation complete")
    except subprocess.CalledProcessError:
        return False
    return True
