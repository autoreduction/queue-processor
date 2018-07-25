setlocal EnableDelayedExpansion
@echo off

REM This script requires 7zip to be installed and in the system path.
REM If you do not have 7zip you can download it from: https://www.7-zip.org/download.html

REM Download and extract
REM target path include \ eg. C:\
set target_path=%1
set path_to_7z=%2
set folder=%target_path%
set destination=%folder%\icat.tar.gz
if not exist %folder% (
    md %folder%
)



if not exist %destination%\setup.py (
    powershell -Command "(new-object System.Net.WebClient).DownloadFile('https://icatproject.org/misc/python-icat/download/python-icat-0.13.1.tar.gz', '"%destination%"')"
    %path_to_7z%\7z e %destination% -o%folder%\icat.tar
    %path_to_7z%\7z x %folder%\icat.tar -o%folder%
    rd /s /q %folder%\icat.tar
) else (
    echo "ICAT files already detected in this location"
)

REM install:
cd %folder%\python-icat-0.13.1
python setup.py build
python setup.py install