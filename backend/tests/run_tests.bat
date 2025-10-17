@echo off
REM Windows批处理脚本 - 运行RAG系统测试

echo ======================================
echo RAG系统测试运行器
echo ======================================
echo.

REM 激活conda环境
echo 激活conda环境...
call conda activate ragchatbot
if %errorlevel% neq 0 (
    echo 错误: 无法激活conda环境 'ragchatbot'
    echo 请确保已安装conda环境
    pause
    exit /b 1
)

REM 检查pytest是否已安装
echo 检查pytest...
python -c "import pytest" 2>nul
if %errorlevel% neq 0 (
    echo pytest未安装，正在安装测试依赖...
    pip install pytest pytest-cov pytest-asyncio pytest-mock httpx
    if %errorlevel% neq 0 (
        echo 错误: 安装测试依赖失败
        pause
        exit /b 1
    )
)

echo.
echo 测试依赖已就绪
echo ======================================
echo.

REM 切换到项目根目录
cd ..\..

REM 根据参数选择测试模式
if "%1"=="" goto :default_test
if "%1"=="all" goto :all_tests
if "%1"=="api" goto :api_tests
if "%1"=="coverage" goto :coverage_test
if "%1"=="quick" goto :quick_test
goto :help

:default_test
echo 运行所有测试...
pytest backend/tests -v
goto :end

:all_tests
echo 运行所有测试（详细模式）...
pytest backend/tests -v -s
goto :end

:api_tests
echo 运行API端点测试...
pytest backend/tests/test_api_endpoints.py -v -m api
goto :end

:coverage_test
echo 运行测试并生成覆盖率报告...
pytest backend/tests --cov=backend --cov-report=html --cov-report=term-missing
echo.
echo 覆盖率报告已生成到 htmlcov/index.html
echo 打开报告...
start htmlcov\index.html
goto :end

:quick_test
echo 运行快速测试（跳过慢速测试）...
pytest backend/tests -v -m "not slow"
goto :end

:help
echo.
echo 用法: run_tests.bat [选项]
echo.
echo 选项:
echo   (无参数)   - 运行所有测试
echo   all       - 运行所有测试（详细输出）
echo   api       - 只运行API测试
echo   coverage  - 运行测试并生成覆盖率报告
echo   quick     - 快速测试（跳过慢速测试）
echo   help      - 显示此帮助信息
echo.
goto :end

:end
echo.
echo ======================================
echo 测试完成
echo ======================================
pause
