"""
Settings for install directories
"""
import os

INSTALL_DIRS = {}

if os.name == 'nt':
    INSTALL_DIRS['activemq'] = 'C:\\activemq\\'
    INSTALL_DIRS['icat'] = 'C:\\icat\\'
    INSTALL_DIRS['mantid'] = 'C:\\mantid\\'
    INSTALL_DIRS['7zip'] = 'C:\\7zip\\'
    INSTALL_DIRS['7zip-location'] = 'C:\\Program Files\\7-Zip'
else:
    INSTALL_DIRS['activemq'] = '/opt/activemq/'
    INSTALL_DIRS['icat'] = '/opt/icat/'
    INSTALL_DIRS['mantid'] = '/opt/mantid/'
