# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
"""
Settings for install directories
"""
import os

if os.name == 'nt':
    # WINDOWS SETTINGS
    INSTALL_DIRS = {
        'activemq': 'C:\\autoreduction_deps\\activemq\\',
        'mantid': 'C:\\autoreduction_deps\\mantid\\',
        '7zip': 'C:\\autoreduction_deps\\7zip\\',
        '7zip-location': 'C:\\Program Files\\7-Zip',  # Expected install location of 7Zip
    }
else:
    # LINUX SETTINGS
    INSTALL_DIRS = {
        'activemq': '/opt/autoreduce_deps/activemq',
        'mantid': '/opt/Mantid'
    }
    # 7Zip not required on linux

# Note the apache-activemq version number in path joined below, must match that in
# build/install/activemq.sh (and activemq.bat), which by default should be true 
ACTIVEMQ_EXECUTABLE = os.path.join(INSTALL_DIRS['activemq'],
                                   'apache-activemq-5.15.9', 'bin',
                                   'activemq')
