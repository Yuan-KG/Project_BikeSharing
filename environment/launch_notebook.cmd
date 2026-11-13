@echo off
setlocal
cd /d "%~dp0.."
set "JUPYTER_PATH=%CD%\work"
"E:\Anaconda3\python.exe" environment\register_kernel.py
"E:\Anaconda3\python.exe" -m jupyter notebook BikeSharing_2024_2025.ipynb
endlocal
