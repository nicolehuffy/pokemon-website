@echo off
cd /d "%~dp0"
python build_mirror.py
if errorlevel 1 pause
python server.py
if errorlevel 1 pause
