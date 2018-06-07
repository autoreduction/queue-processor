"""
Python wraps to windows/linux install scripts for services
"""
import os
import subprocess

from build.install.settings import INSTALL_DIRS
from build.utils.process_runner import run_process_and_log

PATH_TO_DIR = os.path.dirname(os.path.realpath(__file__))


def install_service(service_name, logger):
    """
    Given a service name, find the correct install script, run it and return boolean for success
    :param service_name: The name of the service to install
    :param logger: Handler for logging
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
        logger.info("Installing %s with script %s" % (service_name, install_script))
        run_process_and_log([install_script, install_path, unzip_path], logger)
    except subprocess.CalledProcessError:
        logger.error("Error encountered when installing %s. "
                     "Check the build.log for more information." % service_name)
        return False
    logger.info("%s installed successfully" % service_name)
    return True
