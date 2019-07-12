"""
Used to test that basic mantid functionality can be used
"""
# pylint:skip-file
import sys
import os

from mantid.simpleapi import CreateEmptyTableWorkspace, SaveNexusProcessed


def reduce(input_file, output_dir):
    file_name = os.path.join(output_dir, input_file)
    ws = CreateEmptyTableWorkspace()
    SaveNexusProcessed(InputWorkspace=ws,
                       Filename=file_name)


if __name__ == "__main__":
    reduce(sys.argv[1], sys.argv[2])