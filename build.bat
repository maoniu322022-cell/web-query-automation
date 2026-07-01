@echo off
REM PyInstaller 打包脚本
REM 使用方法：双击运行此文件，自动生成 .exe

echo.
echo ======================================
echo   开始生成可执行文件...
echo ======================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] 未检测到 Python！
    echo [*] 请先安装 Python 3.8+，并勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [✓] 检测到 Python...
echo.

REM 检查 PyInstaller 是否安装
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] 正在安装 PyInstaller...
    pip install -U pyinstaller
    if %errorlevel% neq 0 (
        echo [X] PyInstaller 安装失败！
        pause
        exit /b 1
    )
)

echo [✓] PyInstaller 已就绪
echo.
echo [*] 正在生成 .exe 文件，请稍候...
echo [*] 这可能需要 1-3 分钟...
echo.

REM 运行打包
pyinstaller build.spec --distpath .

if %errorlevel% equ 0 (
    echo.
    echo ======================================
    echo   [✓] 生成成功！
    echo ======================================
    echo.
    echo   文件位置: 本文件夹下的 dist 文件夹
    echo.
    echo   使用方法:
    echo   1. 找到 dist 文件夹
    echo   2. 把整个文件夹复制到其他电脑
    echo   3. 在其他电脑上运行 开始查询.exe
    echo   4. 无需安装 Python！
    echo.
) else (
    echo.
    echo ======================================
    echo   [X] 生成失败！
    echo ======================================
    echo.
)

pause
