@echo off
setlocal
cd /d "%~dp0"
if exist "%WINDIR%\Fonts" set "QT_QPA_FONTDIR=%WINDIR%\Fonts"

set "PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    where py >nul 2>nul
    if errorlevel 1 (
        where python >nul 2>nul
        if errorlevel 1 goto no_python
        python -c "import sys; raise SystemExit(sys.version_info < (3, 11))"
        if errorlevel 1 goto need_python
        python -m venv .venv
    ) else (
        py -3.11 -m venv .venv
    )
    if errorlevel 1 goto setup_failed
)

"%PYTHON%" -c "import PySide6, can, cantools" >nul 2>nul
if errorlevel 1 (
    echo Installing BCM Simulator dependencies into .venv...
    "%PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto setup_failed
    "%PYTHON%" -m pip install -e .
    if errorlevel 1 goto setup_failed
)

"%PYTHON%" -m bcm_simulator %*
if errorlevel 1 goto run_failed
endlocal
exit /b 0

:no_python
echo Python 3.11 or newer was not found. Install Python and enable the py launcher.
goto failed

:need_python
echo Python 3.11 or newer is required.
goto failed

:setup_failed
echo Environment setup failed. Check the Python installation and network connection.
goto failed

:run_failed
echo The BCM Simulator exited with an error.
goto failed

:failed
pause
endlocal
exit /b 1