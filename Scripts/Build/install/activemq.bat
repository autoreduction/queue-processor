setlocal EnableDelayedExpansion
@echo off

REM This script requires 7zip to be installed and in the system path.
REM If you do not have 7zip you can download it from: https://www.7-zip.org/download.html

REM Download and extract
set target_path=%1
set folder=%target_path%activemq
set destination=%folder%\activmq.tar.gz
if not exist %folder% (
    md %folder%
)

if not exist %destination% (
    powershell -Command "(new-object System.Net.WebClient).DownloadFile('http://www.apache.org/dyn/closer.cgi?filename=/activemq/5.15.3/apache-activemq-5.15.3-bin.tar.gz&action=download', '"%destination%"')"
    7z e %destination% -o%folder%\activemq.tar
    7z x %folder%\activemq.tar -o%folder%
    rd /s /q %folder%\activemq.tar
) else (
    echo "ACTIVEMQ files already detected in this location"
)