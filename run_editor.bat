@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 was not found on PATH.
  echo Install Python from python.org and enable "Add Python to PATH".
  pause
  exit /b 1
)
if not exist "bin\minic_parser.exe" call build_parsers.bat
if errorlevel 1 pause & exit /b 1
python app.py
if errorlevel 1 pause
