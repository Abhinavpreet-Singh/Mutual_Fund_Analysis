@echo off
:: schedule_etl.bat
:: Automates scheduling of the Bluestock Mutual Fund ETL Pipeline on Windows Task Scheduler.
:: Runs every weekday (Mon-Fri) at 8:00 PM.

setlocal Enabledelayedexpansion

:: Define absolute paths based on root directory
set "ROOT_DIR=%~dp0"
:: Remove trailing backslash if present
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
set "SCRIPT_PATH=%ROOT_DIR%\run_pipeline.py"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment python executable not found at:
    echo   %PYTHON_EXE%
    echo Please make sure you have created the .venv and installed requirements.txt first.
    exit /b 1
)

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] Master pipeline script not found at:
    echo   %SCRIPT_PATH%
    exit /b 1
)

echo =======================================================================
echo          BLUESTOCK MF ANALYTICS — ETL PIPELINE SCHEDULER (WINDOWS)
echo =======================================================================
echo.
echo This utility will register a new Scheduled Task in Windows Task Scheduler:
echo   * Task Name:  Bluestock_MF_ETL
echo   * Action:     Runs "run_pipeline.py --fetch-live" using the .venv python
echo   * Schedule:   Every Monday, Tuesday, Wednesday, Thursday, and Friday
echo   * Start Time: 8:00 PM (20:00)
echo.
echo Registers as the current logged-in user.
echo.

schtasks /create /tn "Bluestock_MF_ETL" /tr "\"%PYTHON_EXE%\" \"%SCRIPT_PATH%\" --fetch-live" /sc weekly /d MON,TUE,WED,THU,FRI /st 20:00 /f

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Scheduled Task "Bluestock_MF_ETL" successfully registered!
    echo           You can verify, test, or modify this task in Windows Task Scheduler.
) else (
    echo.
    echo [ERROR] Failed to register the scheduled task. 
    echo         If you received an access denied error, please run this terminal/command prompt as Administrator.
)

pause
