"""
Returns methods which can be used in system tests by Mantid.
This is typically used in lieu of actual reduction processing
"""
from __future__ import print_function
import inspect


def get_source_str(filepath):
    """
    Returns a string whose contents is a python function
    to create a file at the given path
    """
    func_str = inspect.getsource(main)
    func_str = func_str.format(filepath)
    return func_str


# pylint: disable=unused-argument
def main(input_file, output_dir):
    """
    Code which is executed on Mantid to create a file at a given path
    """

    #  We use reflection with the format to force our own params in
    with open({0}, mode="w") as touch_file:
        touch_file.write("hello")
