# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
A collection of tests to validate external requirements:
mantid
activemq
"""
import os
from build.settings import INSTALL_DIRS, ACTIVEMQ_EXECUTABLE


def validate_installs(list_of_services):
    """
    Wrapper function to validate multiple installs
    :param list_of_services: services to validate
    :return: Dictionary of {"service_name": install_validity(true/False)
    """
    service_validity = {}
    for service in list_of_services:
        service = service.lower()
        if service == 'activemq':
            service_validity['activemq'] = _validate_activemq()
        elif service == 'mantid':
            service_validity['mantid'] = _validate_mantid()
        elif service == '7zip':
            service_validity['7zip'] = _validate_7zip()
    return service_validity


def _validate_7zip():
    if os.path.isfile(os.path.join(INSTALL_DIRS['7zip-location'], '7z.exe')):
        return True
    return False


def _validate_activemq():
    """ Validate the existence of the activemq executable"""
    return os.path.isfile(ACTIVEMQ_EXECUTABLE)


def _validate_mantid():
    if os.name == 'nt':
        # No need to validate mantid on windows as it is not required
        return True
    if os.path.isfile(os.path.join('/opt', 'Mantid', 'bin', 'mantidpython')):
        return True
    return False
