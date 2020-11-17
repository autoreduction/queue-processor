-- Create Test user
GRANT ALL PRIVILEGES ON autoreduction.* TO 'test-user'@'127.0.0.1' IDENTIFIED BY 'pass';

-- Create DB
-- ToDo: Add a test to ensure that testing db is in use before table drop
DROP DATABASE IF EXISTS autoreduction;
CREATE DATABASE autoreduction;

