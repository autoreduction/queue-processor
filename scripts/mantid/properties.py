# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Generate a mantid properties file
"""
import os
VALID_INSTRUMENTS = ['ENGINX', 'GEM', 'HRPD', 'MAPS', 'MARI', 'MUSR', 'OSIRIS', 'POLARIS', 'POLREF', 'WISH']

CALIBRATION_DIRECTORIES = [
    r'/home/autoreduce/InstrumentFiles/WISH/Calibration/Cycle_11_4/', r'/isis/NDXENGINX/Instrument/data/cycle_14_3/',
    r'/isis/NDXENGINX/Instrument/data/cycle_15_1/', r'/isis/NDXGEM/Instrument/data/cycle_19_1/',
    r'/isis/NDXMARI/Instrument/data/cycle_19_2/', r'/isis/NDXPOLARIS/Instrument/data/cycle_18_3/'
]

MANTID_TEMPLATE = """
# Sets a list of directories for mantid to also look for data

# Note sure we ever want to set this one, but it would be where
# to look for files other than data, e.g. scripts
#usersearch.directories=

logging.loggers.root.level=debug
#logging.channels.fileFilterChannel.level=0

# By default logging is send to stderr. Here change this to stdout
#logging.channels.consoleChannel.class = StdoutChannel

# Turn off saving to of all autoreduction logs to a log file
# These are instead saved to individual logs for each autoreduction job
#logging.loggers.root.channel.channel2=

# Not used by autoreduction but may be in some circumstances of testing
# the autoreduction system
defaultsave.directory=/home/isisautoreduce/reducetest/

# Usage reporting deabled for autoreduction for now
usagereports.enabled=0

# For autoreduction do not look to see if IDFs been updated for now
UpdateInstrumentDefinitions.OnStartup=0

# Number of cores to have available for threading. A best number to use
# for this will depend on hardware and the types of Mantid jobs run
multiThreaded.MaxCores=6

datasearch.searcharchive=off

datasearch.directories={}

ScriptLocalRepository=/tmp/repo

pythonscripts.directories=/tmp/repo/direct_inelastic/MARI/;/tmp/repo/direct_inelastic/MAPS
"""

# TODO is this used at all?


# pylint:disable=dangerous-default-value
def generate_mantid_properties_file(instruments=VALID_INSTRUMENTS, cycles=['19_3', '19_4']):
    """
    Generate the correct data directories for the given instruments and cycles
    :param instruments: All instruments to create directories for
    :param cycles: All cycles to create directories for
    """
    dir_template = r'/isis/NDX{}/Instrument/data/cycle_{}/'
    data_dirs = []
    for instrument in instruments:
        for cycle in cycles:
            data_dirs.append(dir_template.format(instrument, cycle))
    data_search_dirs = data_dirs + CALIBRATION_DIRECTORIES
    data_search_dirs_str = ';'.join(data_search_dirs)
    with open(os.path.join(os.getcwd(), 'Mantid.user.properties'), 'w') as mantid_prop_file:
        mantid_prop_file.write(MANTID_TEMPLATE.format(data_search_dirs_str))


if __name__ == "__main__":
    generate_mantid_properties_file()  # pragma: no cover
