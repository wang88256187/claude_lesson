@echo off
REM 代码质量检查脚本

echo ========================================
echo 运行代码质量检查工具
echo ========================================
echo.

echo [1/4] 运行 isort 检查导入排序...
isort --check-only backend
if %errorlevel% neq 0 (
    echo [错误] isort 检查失败
    echo 运行 'isort backend' 来自动修复
    set FAILED=1
)
echo.

echo [2/4] 运行 Black 检查代码格式...
black --check backend
if %errorlevel% neq 0 (
    echo [错误] Black 检查失败
    echo 运行 'black backend' 来自动修复
    set FAILED=1
)
echo.

echo [3/4] 运行 flake8 代码质量检查...
flake8 backend
if %errorlevel% neq 0 (
    echo [错误] Flake8 检查失败
    set FAILED=1
)
echo.

echo [4/4] 显示代码统计...
echo Backend Python 文件数量:
dir /s /b backend\*.py | find /c ".py"
echo.

if defined FAILED (
    echo ========================================
    echo 代码质量检查失败！请修复上述问题。
    echo ========================================
    exit /b 1
) else (
    echo ========================================
    echo 所有检查通过！✓
    echo ========================================
)
