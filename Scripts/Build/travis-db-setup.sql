# Create Test user
CREATE USER IF NOT EXISTS 'test-user'@'localhost' IDENTIFIED BY 'pass';
GRANT ALL ON autoreduction.* TO 'test-user'@'localhost';

# Create DB
DROP DATABASE IF EXISTS autoreduction;
CREATE DATABASE autoreduction;
