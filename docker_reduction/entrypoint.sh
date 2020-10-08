#!/bin/bash

service mysql start
mysql < build/database/reset_autoreduction_db.sql
python3 setup.py database
# we go into bash to keep the container alive
# otherwise after the database is set up the container exits
# and gets closed - perhaps this should use mysqld but just
# running mysqld will error as we have already started the
# mysql service with `service mysql start`
exec bash
