@echo off
REM ===========================================
REM 投资理财管理系统 - 数据库备份脚本 (Windows)
REM ===========================================
REM 使用方法: 双击运行或在命令行执行 backup_db.bat
REM 建议配置 Windows 任务计划程序每日自动执行
REM ===========================================

setlocal EnableDelayedExpansion

REM 配置变量（请根据实际情况修改）
set DB_NAME=myapp
set DB_USER=devuser
set DB_PASS=YOUR_PASSWORD_HERE
set BACKUP_DIR=.\backup
set KEEP_DAYS=7

REM 创建备份目录
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 生成备份文件名
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATE=%%a%%b%%c
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a%%b
set BACKUP_FILE=%BACKUP_DIR%\%DB_NAME%_%DATE%_%TIME%.sql

REM 执行备份
echo 开始备份数据库: %DB_NAME%
mysqldump -u %DB_USER% -p%DB_PASS% --single-transaction --routines --triggers %DB_NAME% > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo 备份成功: %BACKUP_FILE%
    REM 压缩备份（需要安装 gzip 或使用 7zip）
    REM gzip "%BACKUP_FILE%"
) else (
    echo 备份失败！请检查数据库连接配置
    del "%BACKUP_FILE%"
    exit /b 1
)

REM 清理过期备份
echo 清理超过 %KEEP_DAYS% 天的旧备份...
forfiles /p "%BACKUP_DIR%" /m *.sql /d -%KEEP_DAYS% /c "cmd /c del @path"

REM 显示备份列表
echo 当前备份文件列表:
dir "%BACKUP_DIR%\*.sql" /o-d

echo 备份完成！
pause