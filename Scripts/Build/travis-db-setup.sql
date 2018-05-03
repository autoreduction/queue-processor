-- Create Test user
GRANT ALL PRIVILEGES ON autoreduction.* TO 'user'@'localhost' IDENTIFIED BY 'pass';

-- Create DB
DROP DATABASE IF EXISTS autoreduction;
CREATE DATABASE autoreduction;
