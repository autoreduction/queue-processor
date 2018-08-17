"""
Python wraps to windows/linux install scripts for services
"""
import logging
import os

from build.settings import INSTALL_DIRS
from build.utils.process_runner import run_process_and_log

PATH_TO_DIR = os.path.dirname(os.path.realpath(__file__))


def valid_services():
    """
    :return: A list of all valid services for the operating system
    """
    valid = ['icat', 'activemq', 'mantid']
    if os.name == 'nt':
        valid.append('7zip')
    return valid


def install_service(service_name, log_handler):
    """
    Given a service name, find the correct install script, run it and return boolean for success
    :param service_name: The name of the service to install
    :param log_handler: Handler for logging build info
    :return: True: exit code of installation script was 0
             False: exit code of installation script was non-zero
    """
    install_script = os.path.join(PATH_TO_DIR, (service_name + '.{}'))
    install_path = INSTALL_DIRS[service_name]
    unzip_path = ''
    if os.name == 'nt':
        if service_name == 'mantid':
            # No need to install mantid on windows currently so skip this
            return True
        install_script = install_script.format('bat')
        unzip_path = INSTALL_DIRS['7zip-location']
    else:
        install_script = install_script.format('sh')

    log_handler.logger.info("Installing %s with script %s" % (service_name, install_script))
    if run_process_and_log([install_script, install_path, unzip_path]) is False:
        log_handler.print_and_log("Error encountered when installing %s. "
                                  "Check the build.log for more information." % service_name,
                                  logging.ERROR)
        return False

    log_handler.print_and_log("%s installed successfully" % service_name)
    return True
