"""
Settings for install directories
"""
import os
if os.name == 'nt':
    ACTIVE_MQ_INSTALL_DIR = 'C:\\activemq\\'
    ICAT_INSTALL_DIR = 'C:\\icat\\'
    MANTID_INSTALL_DIR = 'C:\\mantid\\'
else:
    ACTIVE_MQ_INSTALL_DIR = '/opt/activemq/'
    ICAT_INSTALL_DIR = '/opt/icat/'
    MANTID_INSTALL_DIR = '/opt/mantid/'
