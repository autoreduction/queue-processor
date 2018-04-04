"""
Designed to periodically check if the Data Archive for the most recent file.
This file is then compared to the reduction database to see if they are the same.
If not the run should be missing run should be restarted.
"""
import os


class ArchiveMonitor(object):
    """
    Check the data archive location and inspect
    the most recent run data for comparison to the reduction database
    """
    #def __init__(self):


def _find_path_to_current_cycle(instrument_log_path):
    """
    Finds the most recent cycle (current) by inspection of the instrument folder
    Assumes that most recent cycle folder is the final folder in directory
    :param instrument_log_path: The path to the instrument folder given as -
                                "\\isis\inst$\NDX%s\Instrument\log"
    :return: The path to the most recent cycle folder
    """
    #all_folders = os.listdir(instrument_log_path)
    #cycle_folders = [folder for folder in all_folders if folder.startswith('cycle')]

    # List should have most recent cycle at the end
    #most_recent = cycle_folders[-1]