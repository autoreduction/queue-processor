"""
A collection of tests to validate external requirements:
icat
mantid
activemq
"""
import os
import sys
from build.install.settings import INSTALL_DIRS


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
        elif service == 'icat':
            service_validity['icat'] = _validate_icat()
        elif service == 'mantid':
            service_validity['mantid'] = _validate_mantid()
    return service_validity


def _validate_activemq():
    if os.path.isfile(os.path.join(INSTALL_DIRS['activemq'], 'apache-activemq-5.15.3', 'bin', 'activemq')):
        return True
    return False


def _validate_icat():
    try:
        import icat
    except ImportError:
        return False
    return True


def _validate_mantid():
    if os.name == 'nt':
        # No need to validate mantid on windows as it is not required
        return True
    try:
        sys.path.append(os.environ['MANTIDPATH'])
        import mantid.simpleapi
    except ImportError:
        return False
    except KeyError:
        return False
    return True




