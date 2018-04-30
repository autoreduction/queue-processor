# Generate a testing database from the WebApp
python WebApp/autoreduce_webapp/manage.py makemigrations reduction_viewer
python WebApp/autoreduce_webapp/manage.py migrate reduction_viewer