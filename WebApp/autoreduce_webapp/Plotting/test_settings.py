# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Holds access information for the CEPH data store at ISIS
"""

# CEPH access credentials
user_name = None
password = None
host = None

# ToDo: ONLY GEM SO FAR
# The template for where we expect files to b located on CEPH -
template = '/instrument/{}/RBNumber/RB{}/autoreduced/cycle_{}/autoreduce/GEM{}.nxs'

# local path to put files
local_path = None

