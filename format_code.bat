@echo off
REM 自动格式化代码脚本

echo ========================================
echo 自动格式化代码
echo ========================================
echo.

echo [1/2] 运行 isort 排序导入语句...
isort backend
if %errorlevel% neq 0 (
    echo [错误] isort 运行失败
    exit /b 1
)
echo ✓ isort 完成
echo.

echo [2/2] 运行 Black 格式化代码...
black backend
if %errorlevel% neq 0 (
    echo [错误] Black 运行失败
    exit /b 1
)
echo ✓ Black 完成
echo.

echo ========================================
echo 代码格式化完成！
echo ========================================
echo.
echo 现在运行质量检查...
call quality_check.bat
