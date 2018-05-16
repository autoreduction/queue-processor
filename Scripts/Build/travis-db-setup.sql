-- Create Test user
GRANT ALL PRIVILEGES ON autoreduction.* TO 'test-user'@'localhost' IDENTIFIED BY 'pass';

-- Create DB
CREATE DATABASE IF NOT EXISTS autoreduction;
