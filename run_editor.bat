@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=python"
python -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
if errorlevel 1 set "PYTHON=py -3"
%PYTHON% -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or newer was not found on PATH.
  echo Install Python from python.org and enable "Add Python to PATH".
  pause
  exit /b 1
)
where gcc >nul 2>nul
if errorlevel 1 (
  echo GCC was not found on PATH.
  echo Install MinGW-w64 and add its bin folder to PATH.
  pause
  exit /b 1
)
if not exist "bin\minic_parser.exe" call build_parsers.bat
if not exist "bin\minisql_parser.exe" call build_parsers.bat
if errorlevel 1 pause & exit /b 1
%PYTHON% app.py
if errorlevel 1 pause
