#!/bin/bash

service mysql start
mysql < build/database/reset_autoreduction_db.sql
python3 setup.py database
exec bash