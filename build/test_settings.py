# pylint: skip-file
"""
Settings for install directories
"""
import os

if os.name == 'nt':
    # WINDOWS SETTINGS
    INSTALL_DIRS = {
        'activemq': 'C:\\autoreduction_deps\\activemq\\',
        'icat': 'C:\\autoreduction_deps\\icat\\',
        'mantid': 'C:\\autoreduction_deps\\mantid\\',
        '7zip': 'C:\\autoreduction_deps\\7zip\\',
        '7zip-location': 'C:\\Program Files\\7-Zip',  # Expected install location of 7Zip
    }
else:
    # LINUX SETTINGS
    INSTALL_DIRS = {
        'activemq': '/opt/autoreduce_deps/activemq',
        'icat': '/opt/autoreduce_deps/icat',
        'mantid': '/opt/autoreduce_deps/mantid'
    }
    # 7Zip not required on linux

DB_ROOT_PASSWORD = ''
