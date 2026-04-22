@echo off
REM Install Proto — The Proactive Agent — as Windows services using NSSM.
REM Run as Administrator. Requires: nssm in PATH, Python 3.11+, Node 18+.

setlocal
set ROOT=%~dp0
set ROOT=%ROOT:~0,-1%
set PY=python
set NODE=node
set LOGS=%ROOT%\logs

if not exist "%LOGS%" mkdir "%LOGS%"

echo === Installing ProtoAgent ===
nssm install ProtoAgent "%PY%" "%ROOT%\main.py"
nssm set ProtoAgent AppDirectory "%ROOT%"
nssm set ProtoAgent AppStdout "%LOGS%\agent_stdout.log"
nssm set ProtoAgent AppStderr "%LOGS%\agent_stderr.log"
nssm set ProtoAgent AppRestartDelay 5000
nssm set ProtoAgent Start SERVICE_AUTO_START
nssm set ProtoAgent AppEnvironmentExtra PYTHONUNBUFFERED=1 AGENT_HOME=%ROOT%

echo === Installing ProtoWatchdog ===
nssm install ProtoWatchdog "%PY%" "%ROOT%\watchdog\monitor.py"
nssm set ProtoWatchdog AppDirectory "%ROOT%"
nssm set ProtoWatchdog AppStdout "%LOGS%\watchdog_stdout.log"
nssm set ProtoWatchdog AppStderr "%LOGS%\watchdog_stderr.log"
nssm set ProtoWatchdog AppRestartDelay 5000
nssm set ProtoWatchdog Start SERVICE_AUTO_START
nssm set ProtoWatchdog AppEnvironmentExtra PYTHONUNBUFFERED=1 AGENT_HOME=%ROOT%

echo === Installing ProtoAPI ===
nssm install ProtoAPI "%PY%" "%ROOT%\start_api.py"
nssm set ProtoAPI AppDirectory "%ROOT%"
nssm set ProtoAPI AppStdout "%LOGS%\api_stdout.log"
nssm set ProtoAPI AppStderr "%LOGS%\api_stderr.log"
nssm set ProtoAPI AppRestartDelay 5000
nssm set ProtoAPI Start SERVICE_AUTO_START
nssm set ProtoAPI AppEnvironmentExtra PYTHONUNBUFFERED=1 AGENT_HOME=%ROOT%

echo === Installing ProtoWhatsApp ===
nssm install ProtoWhatsApp "%NODE%" "%ROOT%\whatsapp\index.js"
nssm set ProtoWhatsApp AppDirectory "%ROOT%\whatsapp"
nssm set ProtoWhatsApp AppStdout "%LOGS%\whatsapp_stdout.log"
nssm set ProtoWhatsApp AppStderr "%LOGS%\whatsapp_stderr.log"
nssm set ProtoWhatsApp AppRestartDelay 5000
nssm set ProtoWhatsApp Start SERVICE_AUTO_START

echo === Starting services ===
nssm start ProtoAPI
nssm start ProtoWatchdog
nssm start ProtoAgent
nssm start ProtoWhatsApp

echo.
echo All services installed and started.
echo   Agent API   : http://localhost:8000  (docs at /docs)
echo   Dashboard   : http://localhost:3000  (run 'npm run start' in the dashboard folder)
echo   WhatsApp bot: see %LOGS%\whatsapp_stdout.log
echo.
pause
