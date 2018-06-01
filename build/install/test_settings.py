"""
Settings for install directories
"""
import os

INSTALL_DIRS = {}

if os.name == 'nt':
    INSTALL_DIRS['activemq'] = 'C:\\activemq\\'
    INSTALL_DIRS['icat'] = 'C:\\icat\\'
    INSTALL_DIRS['mantid'] = 'C:\\mantid\\'
else:
    INSTALL_DIRS['activemq'] = '/opt/activemq/'
    INSTALL_DIRS['icat'] = '/opt/icat/'
    INSTALL_DIRS['mantid'] = '/opt/mantid/'
