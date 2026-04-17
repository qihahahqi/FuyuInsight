@echo off
REM ===========================================
REM 投资理财管理系统 - Windows 启动脚本
REM ===========================================
REM 使用方法:
REM   start.bat          开发模式启动
REM   start.bat prod     生产模式启动
REM   start.bat init     初始化数据库
REM ===========================================

chcp 65001 >nul
setlocal enabledelayedexpansion

echo =======================================
echo    投资理财管理系统 v1.0.0
echo =======================================

set SCRIPT_DIR=%~dp0
set VENV_PATH=%SCRIPT_DIR%venv
set MODE=%1

REM 检查虚拟环境
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo 正在创建虚拟环境...
    python -m venv "%VENV_PATH%"
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        echo 请确保已安装 Python 3.8+ 并添加到 PATH
        pause
        exit /b 1
    )
    echo √ 虚拟环境创建成功
)

REM 激活虚拟环境
call "%VENV_PATH%\Scripts\activate.bat"

REM 切换到项目目录
cd /d "%SCRIPT_DIR%"

REM 检查依赖
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo 错误: 安装依赖失败
        pause
        exit /b 1
    )
    echo √ 依赖安装完成
)

REM 检查配置文件
if not exist "%SCRIPT_DIR%config\config.yaml" (
    if exist "%SCRIPT_DIR%config\config.yaml.example" (
        echo 配置文件不存在，正在从模板创建...
        copy "%SCRIPT_DIR%config\config.yaml.example" "%SCRIPT_DIR%config\config.yaml" >nul
        echo √ 已创建 config\config.yaml
        echo 请编辑 config\config.yaml 配置数据库和 API Key
    ) else (
        echo 错误: 缺少配置文件模板
        pause
        exit /b 1
    )
)

REM 处理不同模式
if "%MODE%"=="init" (
    echo 正在初始化数据库...
    python init_db.py
    pause
    exit /b %errorlevel%
)

if "%MODE%"=="prod" (
    echo 正在以生产模式启动...
    echo 访问地址: http://localhost:5001
    echo 按 Ctrl+C 停止服务
    python -m gunicorn -c gunicorn_config.py run:app
) else (
    echo 正在以开发模式启动...
    echo 访问地址: http://localhost:5001
    echo 按 Ctrl+C 停止服务
    python run.py
)

pause