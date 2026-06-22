@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo   QunXiaoer Build Tool
echo ========================================
echo.

echo [1/3] Check dependencies...
pip install pyinstaller openai flask pandas python-dotenv -q

echo [2/3] Start building...
pyinstaller build.spec --clean --noconfirm

echo [3/3] Done!
echo.

if exist dist\QunXiaoer.exe (
    echo Build success!
    echo Output: dist\QunXiaoer.exe
    echo.
    echo Usage:
    echo   1. Copy dist\QunXiaoer.exe to target computer
    echo   2. First run will show config wizard
    echo   3. Configure and use
    echo.
    pause
) else (
    echo Build failed! Check error messages.
    pause
)

endlocal
