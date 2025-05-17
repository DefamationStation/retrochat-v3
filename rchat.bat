@echo off
cd /D "%USERPROFILE%\Documents\scripts\Retrochat-v3"
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call .\venv\Scripts\activate.bat
)
echo Retrochat initialized.
python main.py
