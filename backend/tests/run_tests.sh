#!/bin/bash
# Unix/Linux脚本 - 运行RAG系统测试

echo "======================================"
echo "RAG系统测试运行器"
echo "======================================"
echo ""

# 检查pytest是否已安装
echo "检查pytest..."
if ! python -c "import pytest" 2>/dev/null; then
    echo "pytest未安装，正在安装测试依赖..."
    pip install pytest pytest-cov pytest-asyncio pytest-mock httpx
    if [ $? -ne 0 ]; then
        echo "错误: 安装测试依赖失败"
        exit 1
    fi
fi

echo ""
echo "测试依赖已就绪"
echo "======================================"
echo ""

# 切换到项目根目录
cd ../..

# 根据参数选择测试模式
case "$1" in
    "all")
        echo "运行所有测试（详细模式）..."
        pytest backend/tests -v -s
        ;;
    "api")
        echo "运行API端点测试..."
        pytest backend/tests/test_api_endpoints.py -v -m api
        ;;
    "coverage")
        echo "运行测试并生成覆盖率报告..."
        pytest backend/tests --cov=backend --cov-report=html --cov-report=term-missing
        echo ""
        echo "覆盖率报告已生成到 htmlcov/index.html"
        ;;
    "quick")
        echo "运行快速测试（跳过慢速测试）..."
        pytest backend/tests -v -m "not slow"
        ;;
    "help")
        echo ""
        echo "用法: ./run_tests.sh [选项]"
        echo ""
        echo "选项:"
        echo "  (无参数)   - 运行所有测试"
        echo "  all       - 运行所有测试（详细输出）"
        echo "  api       - 只运行API测试"
        echo "  coverage  - 运行测试并生成覆盖率报告"
        echo "  quick     - 快速测试（跳过慢速测试）"
        echo "  help      - 显示此帮助信息"
        echo ""
        ;;
    *)
        echo "运行所有测试..."
        pytest backend/tests -v
        ;;
esac

echo ""
echo "======================================"
echo "测试完成"
echo "======================================"
