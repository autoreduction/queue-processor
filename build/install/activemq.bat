@echo off
setlocal EnableDelayedExpansion

REM This script requires 7zip to be installed and in the system path.
REM If you do not have 7zip you can download it from: https://www.7-zip.org/download.html

REM When updating activemq version also to this in activemq.sh and build/test_settings.py

REM Download and extract
set target_path=%1
set path_to_7z=%2
set folder=%target_path%
set destination=%folder%\activmq.zip
if not exist %folder% (
    md %folder%
)

if not exist %destination% (
    echo Information: Downloading activemq - this could take several minutes
    powershell -Command "(new-object System.Net.WebClient).DownloadFile('https://archive.apache.org/dist/activemq/5.15.9/apache-activemq-5.15.9-bin.zip', '"%destination%"')"
    REM if download failed then file still does not exist
    if not exist %destination% (
        echo Error: Download failed
        exit /b 1
    ) else (
        echo Information: Download complete
        echo Information: Extracting ActiveMQ
        %path_to_7z%\7z x %destination% -o%folder%
        del %destination%
    )
) else (
    echo Information: ActiveMQ files already detected in this location
    echo Information: If validation fails - delete %destination% and re-run this script
)
