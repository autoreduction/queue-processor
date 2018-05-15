#!/usr/bin/env sh
# Clear db and generate db
mysql < Scripts/Build/travis-db-setup.sql

# Generate and perform django migrations from reduction-db to test-db
python WebApp/autoreduce_webapp/manage.py makemigrations reduction_viewer
python WebApp/autoreduce_webapp/manage.py migrate reduction_viewer

# Populate test-db with test data
mysql < Scripts/Build/populate-reduction_viewer-db.sql
