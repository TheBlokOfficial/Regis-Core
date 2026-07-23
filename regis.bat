@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python -m regis_cli.main
