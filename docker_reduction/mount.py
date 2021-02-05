# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
A Class to store information about a docker mount
"""


# pylint:disable=too-few-public-methods
class Mount:
    """ Class to contain information about a docker mount """
    def __init__(self, host_location, container_destination):
        # The location of the directory you wish to mount on the host machine
        self.host_location = host_location
        # The location of the desired destination to mount to on the container
        self.container_destination = container_destination
