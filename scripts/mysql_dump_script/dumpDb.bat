@echo off
for /f "skip=1" %%x in ('wmic os get localdatetime') do if not defined MyDate set MyDate=%%x
set today=%MyDate:~6,2%-%MyDate:~4,2%-%MyDate:~0,4%
set directory=C:\database_backup

mysqldump --single-transaction=TRUE -uusername -ppassword autoreduction > %directory%\sql-%today%.sql

forfiles /P "%directory%" /S /M *.sql /D -7 /C "cmd /c del @PATH"