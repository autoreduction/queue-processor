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


setup_requires = ['attrs==20.2.0',
                  'dash==1.16.3',
                  'dash_html_components==1.1.1',
                  'dash_core_components==1.10.2',
                  'docker==4.3.1',
                  'Django==3.1',
                  'django_extensions==3.0.9',
                  'django_plotly_dash==1.4.2',
                  'django-user-agents==0.4.0',
                  'filelock==3.0.12',
                  'fire==0.3.1',
                  'gitpython==3.1.7',
                  'IPython==7.18.1',
                  'mysqlclient==2.0.1',
                  'mysql-connector==2.2.9',
                  'nexusformat==0.5.3',
                  'numpy==1.19.1',
                  'pandas==1.1.0',
                  'plotly==4.9.0',
                  'pytz==2020.1',
                  'PyMySQL==0.10.1',
                  'pysftp==0.2.9',
                  'python-icat==0.17.0',
                  'requests==2.24.0',
                  'sentry_sdk==0.18',
                  'service_identity==18.1.0',
                  'SQLAlchemy==1.3.20',
                  'stomp.py==6.1.0',
                  'suds-py3==1.4.1.0',
                  'Twisted==20.3.0',
                  'PyYAML==5.3.1']


if platform.system() == 'Windows':
    setup_requires.append('pypiwin32')
else:
    setup_requires.append('python-daemon==2.2.4')


setup(name='AutoReduction',
      version='20.1',
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
