@echo off
cd /d %~dp0
cd ..
call venv\Scripts\activate
cd src
python -m preview.navmesh_preview
cd ..
deactivate