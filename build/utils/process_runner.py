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
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process_output, process_error = process.communicate()
    if process_output:
        print(process_output)
    if process_error:
        print(process_error)
        return False
    return True
