@echo off
start python app.py
timeout /t 5
start http://localhost:5000