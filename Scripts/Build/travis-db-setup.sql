-- Create Test user
CREATE USER IF NOT EXISTS 'test-user'@'localhost' IDENTIFIED BY 'pass';

-- Create DB
DROP DATABASE IF EXISTS autoreduction;
CREATE DATABASE autoreduction;
