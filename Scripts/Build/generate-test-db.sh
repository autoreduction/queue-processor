#!/bin/bash
# Clear db and generate db
mysql < Scripts/Build/travis-db-setup.sql

# Move test_settings.py if not already done
if [ -e WebApp/autoreduce_webapp/autoreduce_webapp/test_settings.py ]
then
    mv WebApp/autoreduce_webapp/autoreduce_webapp/test_settings.py WebApp/autoreduce_webapp/autoreduce_webapp/settings.py 
else
    echo "test_settings not present or already in use"
fi

# Generate and perform django migrations from reduction-db to test-db
python WebApp/autoreduce_webapp/manage.py makemigrations reduction_viewer
python WebApp/autoreduce_webapp/manage.py migrate reduction_viewer

# Populate test-db with test data
mysql < Scripts/Build/populate-reduction_viewer-db.sql
