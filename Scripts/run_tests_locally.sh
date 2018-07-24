#!/usr/bin/bash

# Stop script if any component fails
set -e

current_dir=$PWD

# Check if scripts is present in the current path and exit
if [[ $current_dir = *[Ss]cripts* ]]; then
  echo "This script must be run from the repository root. Exiting."
  exit -1
fi

# Get username if required
while getopts :du: arg; do
  case "${arg}" in
    u)
      username=${OPTARG}
      ;;
	d)
	  drop_db=true
	  ;;
  esac
done

# Get mysql command prefix

if [ -n "${username}" ]; then
  mysql="mysql -u $username "
else
  mysql="mysql "
fi

run_mysql_command(){
	command="$mysql $1"
	eval $command
}

if [ -n "${drop_db}" ]; then
  # Drop DB if requested
  echo "Dropping DB"
  run_mysql_command "--execute=\"Drop Database autoreduction;\""
fi

# Setup DB and run all migrations
run_mysql_command "< Scripts/Build/database/travis-db-setup.sql"
./Scripts/Build/project/migrate_test_settings.sh
./Scripts/Build/database/generate_testing_database.sh

# Add test data
run_mysql_command "mysql < Scripts/Build/database/populate-reduction_viewer-db.sql"
nosetests Scripts/Build/tests/test_db_generation.py

# Run nose tests
nosetests utils/clients/tests
nosetests WebApp/autoreduce_webapp/test

# Static analysis - Last as it is slowest
./Scripts/Build/tests/test_pylint.sh