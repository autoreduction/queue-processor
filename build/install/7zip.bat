@echo off
setlocal EnableDelayedExpansion

REM Download and extract
set target_path=%1
REM path_to_7z is unused but still passed to this function for simplification of install_services
set path_to_7z=%2
set folder=%target_path%
set destination=%folder%\7zip.exe
if not exist %folder% (
    md %folder%
)

if not exist %destination% (
    powershell -Command "(new-object System.Net.WebClient).DownloadFile('https://www.7-zip.org/a/7z1805-x64.exe', '"%destination%"')"
) else (
    echo 7zip installer already downloaded at %destination%
)

START /WAIT %destination%
del %destination%
del /F /Q %folder%
echo 7zip installed