# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
All functionality for access of SFTP locations
"""
import pysftp
import settings as sftp_settings


class SFTPAccess(object):

    @staticmethod
    def get_file(instrument, rb_number, cycle, run_number):
        """
        Locate and download a file from the sftp information held in settings.py
        :param instrument: The instrument the data file was created from
        :param rb_number: The rb (experiment) nm=umber associated with the data file
        :param cycle: The cycle for the run e.g. 19_1
        :param run_number: The run number that identifies the data file
        :return: A file path to where the data is held on the local system
        """
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        data_file_location = sftp_settings.template.format(instrument, rb_number, cycle, run_number)
        with pysftp.Connection(host=sftp_settings.host, username=sftp_settings.user_name,
                               password=sftp_settings.password, cnopts=cnopts) as isis_compute:
            isis_compute.get(remotepath=data_file_location,
                             localpath=sftp_settings.local_path)

