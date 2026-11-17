
@echo off

cd /d "C:\Users\uthra\Dropbox\My PC (DESKTOP-45TREMJ)\Desktop\real-time-data-engineering-pipeline"

"venv\Scripts\python.exe" "scheduler.py" >> "logs\scheduler_task.log" 2>&1
