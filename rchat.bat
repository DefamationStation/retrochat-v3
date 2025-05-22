@echo off
cd /D "%USERPROFILE%\Documents\scripts\retrochat-v3"

if not defined VIRTUAL_ENV (
    echo Setting PowerShell execution policy...
    powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
    
    echo Activating virtual environment...
    powershell -Command "& '.\\.venv\\Scripts\\Activate.ps1'; python main.py"
) else (
    echo Virtual environment already active.
    echo Retrochat initialized.
    python main.py
)