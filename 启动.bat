@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   群小二 - 启动程序
echo ========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [错误] 未找到 Python 环境，请检查 venv 文件夹
    pause
    exit /b 1
)

echo [1/2] 安装依赖（首次可能需要几分钟）...
venv\Scripts\pip install -r requirements.txt -q
echo 依赖安装完成
echo.

echo [2/2] 启动管理后台...
echo.
echo ========================================
echo   浏览器将自动打开 http://localhost:8501
echo   如未打开请手动访问
echo   左侧菜单点 "飞书接入" 进行配置
echo ========================================
echo.

start http://localhost:8501
venv\Scripts\python.exe src\web_nicegui.py

pause
