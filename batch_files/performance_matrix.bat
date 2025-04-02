@echo off
cd /d %~dp0
cd ..
call venv\Scripts\activate
cd src
python -m performance_matrix
cd ..
deactivate