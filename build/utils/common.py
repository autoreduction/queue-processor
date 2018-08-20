"""
Script to hold common varibales used in building the project
"""

from build.utils.build_logger import BuildLogger
from utils.project.structure import get_project_root


def build_logger():
    """ Encapsulate import of git from get_project """
    return BuildLogger(get_project_root())


def validate_user_input(user_input, expected):
    """
    Validates that the user input is what we expect
    :param user_input: Input given by the user (List)
    :param expected: What we expect to get (List)
    :return: True if all are valid, else produce a RuntimeError
    """
    err_msg = "Expected {0} to be of type list not: {1}"
    if not isinstance(user_input, list):
        raise ValueError(err_msg.format('user_input', type(user_input)))
    if not isinstance(expected, list):
        raise ValueError(err_msg.format('expected', type(expected)))
    # cast all to lower case
    user_input = [user_in.lower() for user_in in user_input]
    # validate input
    for item in user_input:
        if item not in expected:
            raise RuntimeError("Input: \'{0}\' is not valid. "
                               "Valid inputs are {1}".format(item, expected))
    return True
