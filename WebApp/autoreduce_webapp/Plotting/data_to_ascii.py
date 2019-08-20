import os
from subprocess import Popen


def transform_data_to_ascii(input_file_path, output_file_dir):
    mantid_script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                      'mantid_to_ascii.py')
    if os.name == ' nt':
        Popen([r'C:\MantidInstall\bin\mantidpython.bat', '--classic', mantid_script_path,
               input_file_path, output_file_dir])
