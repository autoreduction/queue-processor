# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
The mount information required by Mantid
"""

from docker_reduction.mount import Mount

# On production this will be the base directory of the ISIS data archive (/isis)
DATA_IN = Mount(host_location='/isis/', container_destination='/isis/')

# On production this will be the base directory of CEPH (/instrument)
DATA_OUT = Mount(host_location='/instrument/', container_destination='/instrument/')
