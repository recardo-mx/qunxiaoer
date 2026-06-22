@echo off
chcp 65001 >nul
setlocal

if "%1"=="" goto all
if "%1"=="check" goto check
if "%1"=="test" goto test
if "%1"=="bot" goto bot
if "%1"=="desktop" goto desktop
if "%1"=="web" goto web
if "%1"=="all" goto all
if "%1"=="help" goto help

echo Unknown command: %1
goto help

:check
echo [INFO] Check dependencies...
pip install -r requirements.txt -q
echo [INFO] Check config...
if not exist .env (
    echo [WARN] .env not found, creating from example...
    copy .env.example .env
    echo [WARN] Please edit .env to configure Feishu and LLM
    pause
    exit /b 1
)
echo [INFO] Check done
goto end

:test
echo [INFO] Test LLM connection...
python src\main.py test
goto end

:bot
echo [INFO] Start Feishu bot service...
python src\main.py bot
goto end

:desktop
echo [INFO] Start desktop GUI...
python src\main.py desktop
goto end

:web
echo [INFO] Start web admin...
python src\main.py web
goto end

:all
echo [INFO] Start all services...
python src\main.py all
goto end

:help
echo QunXiaoer - Community Message Analysis System
echo.
echo Usage: run.bat [command]
echo.
echo Commands:
echo   check     Check environment and config
echo   test      Test LLM connection
echo   bot       Start Feishu bot service
echo   desktop   Start desktop GUI
echo   web       Start web admin
echo   all       Start all services (default)
echo   help      Show this help
goto end

:end
endlocal
