"""
Wrapper for running subprocesses
"""

import subprocess


def run_process_and_log(list_of_args, logger):
    """
    Call a process using Popen and logs output to file
    :param list_of_args: list of arguments for Popen
    :param logger: log handler
    """
    process = subprocess.Popen(list_of_args,
                               stderr=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    process_output, _ = process.communicate()
    if process_output:
        logger.info(process_output)
