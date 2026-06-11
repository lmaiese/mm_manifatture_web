@echo off
REM =====================================================================
REM  MM Manifatture - avvio automatico bot Telegram (Task Scheduler)
REM  Pensato per essere lanciato come Action di un task "At log on".
REM =====================================================================

setlocal

REM 1) Working directory = cartella di questo script (bot/)
cd /d "%~dp0"

REM Timestamp per il file di log (indipendente dal locale, via PowerShell)
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%i"

if not exist "logs" mkdir "logs"
set "LOGFILE=logs\launcher_%TS%.log"

echo ==================================================================== >> "%LOGFILE%"
echo [%DATE% %TIME%] Avvio launcher MM Manifatture bot                     >> "%LOGFILE%"
echo Working dir: %CD%                                                     >> "%LOGFILE%"

REM 2) Venv del progetto
set "VENV_DIR=%~dp0.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [%TIME%] ERRORE: venv non trovato in "%VENV_PY%" >> "%LOGFILE%"
    exit /b 1
)

REM Attiva il venv (imposta VIRTUAL_ENV/PATH per coerenza con l'ambiente)
call "%VENV_DIR%\Scripts\activate.bat"

echo [%TIME%] Python venv: %VENV_PY% >> "%LOGFILE%"

REM 3) Installa/aggiorna dipendenze (pip e' idempotente: salta i pacchetti
REM    gia' soddisfatti, quindi e' sicuro eseguirlo ad ogni avvio).
echo [%TIME%] pip install -r requirements.txt ... >> "%LOGFILE%"
"%VENV_PY%" -m pip install -r requirements.txt >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo [%TIME%] ATTENZIONE: pip install ha restituito un errore, vedi sopra. Provo comunque ad avviare il bot. >> "%LOGFILE%"
)

REM 4) Avvio del bot (processo in foreground - polling Telegram, resta attivo)
echo [%TIME%] Avvio bot (src\main.py)... >> "%LOGFILE%"
"%VENV_PY%" -m src.main >> "%LOGFILE%" 2>&1

set "EXITCODE=%ERRORLEVEL%"
echo [%TIME%] Bot terminato con exit code %EXITCODE% >> "%LOGFILE%"
echo ==================================================================== >> "%LOGFILE%"

endlocal
exit /b %EXITCODE%
