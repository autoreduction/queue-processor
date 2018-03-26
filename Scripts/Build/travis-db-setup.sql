# Create Test user
CREATE USER 'test-user'@'localhost' IDENTIFIED BY 'pass';
GRANT ALL ON autoreduction.* TO 'test-user'@'localhost';
