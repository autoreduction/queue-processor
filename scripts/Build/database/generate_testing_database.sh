#!/usr/bin/env sh
# Generate a testing database from WebApp migrations
_PATH_TO_MANAGE="WebApp/autoreduce_webapp/manage.py"
python ${_PATH_TO_MANAGE} migrate admin
python ${_PATH_TO_MANAGE} migrate sessions
python ${_PATH_TO_MANAGE} migrate auth
python ${_PATH_TO_MANAGE} makemigrations reduction_viewer
python ${_PATH_TO_MANAGE} migrate reduction_viewer
python ${_PATH_TO_MANAGE} makemigrations reduction_variables
python ${_PATH_TO_MANAGE} migrate reduction_variables

# Add the super user required for development mode testing
echo "from django.contrib.auth.models import User;
User.objects.filter(username='super').delete();
User.objects.create_superuser('super', '', 'super')" | python ${_PATH_TO_MANAGE} shell