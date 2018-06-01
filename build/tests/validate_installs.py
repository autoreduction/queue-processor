"""
A collection of tests to validate external requirements:
icat
mantid
activemq
"""
import os
import sys


def validate_icat():
    try:
        import icat
    except ImportError:
        return False
    return True


def validate_mantid():
    sys.path.append(os.environ['MANTIDPATH'])
    try:
        import mantid.simpleapi
    except ImportError:
        return False
    return True


def validate_activemq():
    # Try start the service
    # Try to use client to access the service
    return False

