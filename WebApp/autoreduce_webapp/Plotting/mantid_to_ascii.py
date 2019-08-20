import sys
import os

from mantid.simpleapi import Load, SaveAscii


def main(input_file, output_directory):
    workspace = Load(input_file)
    SaveAscii(workspace[0], os.path.join(output_directory, 'data.csv'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
