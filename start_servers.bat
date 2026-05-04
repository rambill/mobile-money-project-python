@echo off
REM Start all configured servers in localhost mode (Windows)

echo Starting Distributed Mobile Money Servers...
echo ==============================================

REM Create data directories
if not exist data mkdir data
if not exist wal mkdir wal

REM Start each server in separate window
start "MoMo Server 1" python server.py 1
timeout /t 1 /nobreak > nul

start "MoMo Server 2" python server.py 2
timeout /t 1 /nobreak > nul

start "MoMo Server 3" python server.py 3

echo.
echo All servers started in separate windows!
echo ==============================================
echo.
echo To stop servers, close the server windows or press Ctrl+C
echo To run client: python client.py
echo To check status: python admin.py status
echo.
