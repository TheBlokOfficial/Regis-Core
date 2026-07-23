@echo off
uvicorn apps.controller.main:app --host 0.0.0.0 --port 8000
pause
