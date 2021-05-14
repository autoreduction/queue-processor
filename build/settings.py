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
    # Adding this as we no longer have any nodes running on Windows.
    # The change will appear in https://github.com/ISISScientificComputing/autoreduce/pull/1033
    # If Windows must be used you will have to redefine the variables from below
    raise RuntimeError("Running the install commands on Windows is no longer expected, nor actively supported.")
else:
    # LINUX SETTINGS
    INSTALL_DIRS = {'activemq': '/opt/autoreduce_deps/activemq', 'mantid': '/opt/Mantid'}
    # 7Zip not required on linux

# Note the apache-activemq version number in path joined below, must match that in
# build/install/activemq.sh (and activemq.bat), which by default should be true
ACTIVEMQ_EXECUTABLE = os.path.join(INSTALL_DIRS['activemq'], 'apache-activemq-5.15.9', 'bin', 'activemq')
