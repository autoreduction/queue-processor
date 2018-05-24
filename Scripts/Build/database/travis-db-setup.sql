-- Create Test user
GRANT ALL PRIVILEGES ON autoreduction.* TO 'test-user'@'localhost' IDENTIFIED BY 'pass';

-- Create DB
DROP DATABASE IF EXISTS autoreduction;
CREATE DATABASE autoreduction;
