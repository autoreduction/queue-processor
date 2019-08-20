import os

import settings as sftp_settings
from data_access import SFTPAccess
from data_to_ascii import transform_data_to_ascii


def extract_plotting_data(instrument, rb_number, cycle, run_number):
    sftp_client = SFTPAccess()
    sftp_client.get_file(instrument.upper(), rb_number, cycle, run_number)
    transform_data_to_ascii(sftp_settings.local_path, os.path.dirname(sftp_settings.local_path))
