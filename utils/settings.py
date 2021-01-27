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

from utils.project.structure import get_project_root
from utils.clients.settings.client_settings_factory import ClientSettingsFactory

VALID_INSTRUMENTS = ['ENGINX', 'GEM', 'HRPD', 'MAPS', 'MARI', 'MUSR', 'OSIRIS', 'POLARIS', 'POLREF', 'WISH']

CONFIG = configparser.ConfigParser()
INI_FILE = os.path.join(get_project_root(), 'utils', 'credentials.ini')
CONFIG.read(INI_FILE)


def get_str(section, key):
    return str(CONFIG.get(section, key, raw=True))  # raw=True to allow strings with special characters to be passed


SETTINGS_FACTORY = ClientSettingsFactory()

ICAT_SETTINGS = SETTINGS_FACTORY.create('icat',
                                        username=get_str('ICAT', 'user'),
                                        password=get_str('ICAT', 'password'),
                                        host=get_str('ICAT', 'host'),
                                        port='',
                                        authentication_type=get_str('ICAT', 'auth'))

MYSQL_SETTINGS = SETTINGS_FACTORY.create('database',
                                         username=get_str('DATABASE', 'user'),
                                         password=get_str('DATABASE', 'password'),
                                         host=get_str('DATABASE', 'host'),
                                         port=get_str('DATABASE', 'port'),
                                         database_name=get_str('DATABASE', 'name'))

ACTIVEMQ_SETTINGS = SETTINGS_FACTORY.create('queue',
                                            username=get_str('QUEUE', 'user'),
                                            password=get_str('QUEUE', 'password'),
                                            host=get_str('QUEUE', 'host'),
                                            port=get_str('QUEUE', 'port'))

LOCAL_MYSQL_SETTINGS = SETTINGS_FACTORY.create('database',
                                               username=get_str('DATABASE', 'user'),
                                               password=get_str('DATABASE', 'password'),
                                               host=get_str('DATABASE', 'host'),
                                               port=get_str('DATABASE', 'port'))

SFTP_SETTINGS = SETTINGS_FACTORY.create('sftp',
                                        username=get_str('SFTP', 'user'),
                                        password=get_str('SFTP', 'password'),
                                        host=get_str('SFTP', 'host'),
                                        port=get_str('SFTP', 'port'))

CYCLE_SETTINGS = SETTINGS_FACTORY.create('cycle',
                                         username=get_str('CYCLE', 'user'),
                                         password=get_str('CYCLE', 'password'),
                                         host='',
                                         port='',
                                         uows_url=get_str('CYCLE', 'uows_url'),
                                         scheduler_url=get_str('CYCLE', 'scheduler_url'))
