# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Paths to data used for testing the project that is not easy to mock / fake e.g. meta data complete nexus file
"""
import os

VALID_NEXUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'WISH101.nxs')
ZERO_BEAM_NEXUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zero_beam.nxs')
