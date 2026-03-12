@echo off
title SkyBook — Flight Booking System
color 0B

echo.
echo  ==========================================
echo   SKY BOOK — Flight Booking System
echo  ==========================================
echo.

echo [1/2] Installing required Python packages...
pip install flask flask-cors flask-jwt-extended bcrypt >nul 2>&1
echo  Packages ready!
echo.

echo [2/2] Starting SkyBook Backend Server...
echo  Backend running at: http://localhost:5000
echo.
echo  Opening frontend in your browser...
start "" skybook_frontend.html
echo.
echo  ==========================================
echo   Demo Login:
echo   Email   : demo@skybook.app
echo   Password: Demo1234!
echo  ==========================================
echo.
echo  Press CTRL+C to stop the server.
echo.

python skybook_backend.py
pause
