"""
Helpers for checking the status of services
These can be used in the service manager at a later stage
"""
from datetime import timedelta


def compare_time(lhs_time, rhs_time, expected_difference):
    """
    Compare one time to another
    :param lhs_time: The time on the left hand side of the minus operation
    :param rhs_time: The time to be subtracted from lhs_time
    :param expected_difference: The expected difference in lhs and rhs in seconds
    :return: If lhs - rhs >= expected_difference
    """
    if lhs_time - rhs_time >= timedelta(seconds=expected_difference):
        return True
    return False
