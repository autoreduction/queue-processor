# pylint:skip-file
"""
Wrapper for the functionality for various installation and project setup commands
see:
    `python setup.py help`
for more details
"""
from setuptools import setup

import platform

from build.commands.database import InitialiseTestDatabase
from build.commands.help import Help
from build.commands.installs import InstallExternals
from build.commands.migrate_settings import MigrateTestSettings
from build.commands.start import Start

setup_requires = ['Django==1.11.12',
                  'django_extensions==2.0.7',
                  'django-user-agents==0.3.2',
                  'gitpython',
                  'MySQL-python==1.2.5',
                  'pytz',
                  'pymysql',
                  'requests==2.18.4',
                  'SQLAlchemy==1.2.7',
                  'mysql-connector==2.1.6',
                  'stomp.py==4.1.20',
                  'suds==0.4',
                  'Twisted==14.0.2',
                  'watchdog==0.8.3']

if platform.system() == 'Windows':
    setup_requires.append('pypiwin32')
else:
    setup_requires.append('python-daemon')


setup(name='AutoReduction',
      version='1.0',
      description='ISIS AutoReduction service',
      author='ISIS Autoreduction Team',
      url='https://github.com/ISISScientificComputing/autoreduce/',
      install_requires=setup_requires,
      cmdclass={
          'test_settings': MigrateTestSettings,
          'database': InitialiseTestDatabase,
          'externals': InstallExternals,
          'start': Start,
          'help': Help,
      },
     )
