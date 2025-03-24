@echo off
cd /d %~dp0
cd ..
call venv\Scripts\activate
cd src
python main.py
cd ..
deactivate