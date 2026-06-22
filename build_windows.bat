@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo   QunXiaoer Windows Build Script
echo ========================================
echo.

echo [1/4] Check Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found, please install Python 3.10+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo Python installed

echo [2/4] Install dependencies...
pip install openai flask pandas python-dotenv pyinstaller -q

echo [3/4] Start building...
pyinstaller --onefile --windowed --name "QunXiaoer" --add-data "data;data" --add-data ".env.example;." src/desktop_gui.py --noconfirm

echo [4/4] Done!
echo.

if exist dist\QunXiaoer.exe (
    echo ========================================
    echo   Build Success!
    echo ========================================
    echo.
    echo Output: dist\QunXiaoer.exe
    echo.
    echo Usage:
    echo   1. Double click QunXiaoer.exe
    echo   2. Config wizard will show
    echo   3. Configure and use
    echo.
    echo Distribution:
    echo   Just send QunXiaoer.exe
    echo.
) else (
    echo Build failed! Check error messages above.
)

pause
