# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
"""
Settings for connecting to the test services that run locally
"""
import configparser
import os

from utils.project.structure import PROJECT_ROOT
from utils.clients.settings.client_settings_factory import ClientSettingsFactory

VALID_INSTRUMENTS = ['ENGINX', 'GEM', 'HRPD', 'MAPS', 'MARI', 'MUSR', 'OSIRIS', 'POLARIS', 'POLREF', 'WISH']

CONFIG = configparser.ConfigParser()
INI_FILE = os.path.join(PROJECT_ROOT, 'utils', 'credentials.ini')
CONFIG.read(INI_FILE)


def get_setting(section, key):
    """
    Gets the value of the key from the section.
    """
    return str(CONFIG.get(section, key, raw=True))  # raw=True to allow strings with special characters to be passed


SETTINGS_FACTORY = ClientSettingsFactory()

ICAT_SETTINGS = SETTINGS_FACTORY.create('icat',
                                        username=get_setting('ICAT', 'user'),
                                        password=get_setting('ICAT', 'password'),
                                        host=get_setting('ICAT', 'host'),
                                        port='',
                                        authentication_type=get_setting('ICAT', 'auth'))

MYSQL_SETTINGS = SETTINGS_FACTORY.create('database',
                                         username=get_setting('DATABASE', 'user'),
                                         password=get_setting('DATABASE', 'password'),
                                         host=get_setting('DATABASE', 'host'),
                                         port=get_setting('DATABASE', 'port'),
                                         database_name=get_setting('DATABASE', 'name'))

ACTIVEMQ_SETTINGS = SETTINGS_FACTORY.create('queue',
                                            username=get_setting('QUEUE', 'user'),
                                            password=get_setting('QUEUE', 'password'),
                                            host=get_setting('QUEUE', 'host'),
                                            port=get_setting('QUEUE', 'port'))

LOCAL_MYSQL_SETTINGS = SETTINGS_FACTORY.create('database',
                                               username=get_setting('DATABASE', 'user'),
                                               password=get_setting('DATABASE', 'password'),
                                               host=get_setting('DATABASE', 'host'),
                                               port=get_setting('DATABASE', 'port'))

SFTP_SETTINGS = SETTINGS_FACTORY.create('sftp',
                                        username=get_setting('SFTP', 'user'),
                                        password=get_setting('SFTP', 'password'),
                                        host=get_setting('SFTP', 'host'),
                                        port=get_setting('SFTP', 'port'))

CYCLE_SETTINGS = SETTINGS_FACTORY.create('cycle',
                                         username=get_setting('CYCLE', 'user'),
                                         password=get_setting('CYCLE', 'password'),
                                         host='',
                                         port='',
                                         uows_url=get_setting('CYCLE', 'uows_url'),
                                         scheduler_url=get_setting('CYCLE', 'scheduler_url'))
