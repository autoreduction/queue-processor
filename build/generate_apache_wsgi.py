"""
Generate the apache_django_wsgi.py file to serve django content from an apache server

Usage:
python generate_apache_wsgi.py path/to/autoreduction/git/dir
e.g.
python generate_apache_wsgi.pt C:\\Users\\...\\git\\autoreduction
"""

import os
import sys


def _generate_conf_file():
    """
    Generates the configuration file using a command line argument
    """
    try:
        root_dir = sys.argv[1]
    except IndexError:
        raise RuntimeError("Root directory argument not given.")
    root_dir = root_dir.strip('/')
    if os.path.isdir(root_dir):
        root_dir = root_dir.replace('\\', '/')
        _write_file(root_dir)
    else:
        raise RuntimeError("Unable to generate apache_django_wsgi.conf."
                           "Root directory: %s -  was invalid" % root_dir)


def _write_file(root_dir):
    apache_dir = os.path.join(root_dir, 'WebApp', 'autoreduce_webapp', 'apache')
    with open(os.path.join(apache_dir, 'apache_django_wsgi.conf.template'), 'r') as template_file:
        with open(os.path.join(apache_dir, 'apache_django_wsgi.conf'), 'w') as output_file:
            for line in template_file:
                output_file.write(line.format(root_dir))


if __name__ == '__main__':
    _generate_conf_file()
