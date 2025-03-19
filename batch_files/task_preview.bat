@echo off
cd /d %~dp0
cd ..
call venv\Scripts\activate
cd src
python -m preview.task_preview
cd ..
deactivate