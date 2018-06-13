"""
Settings for install directories
"""
import os

if os.name == 'nt':
    INSTALL_DIRS = {
        'activemq': 'C:\\activemq\\',
        'icat': 'C:\\icat\\',
        'mantid': 'C:\\mantid\\',
        '7zip': 'C:\\7zip\\',
        '7zip-location': 'C:\\Program Files\\7-Zip',  # Expected install location of 7Zip
    }
else:
    INSTALL_DIRS = {
        'activemq': '/opt/activemq/',
        'icat': '/opt/icat/',
        'mantid': '/opt/mantid/'
    }
    # 7Zip not required on linux

DB_ROOT_PASSWORD = ''
