FROM mysql/mysql-server:latest

ADD build/database/reset_autoreduction_db.sql /reset_autoreduction_db.sql

RUN mysql < /reset_autoreduction_db.sql