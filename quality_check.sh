#!/bin/bash
# 代码质量检查脚本

set -e

echo "========================================"
echo "运行代码质量检查工具"
echo "========================================"
echo ""

FAILED=0

echo "[1/4] 运行 isort 检查导入排序..."
if ! isort --check-only backend; then
    echo "[错误] isort 检查失败"
    echo "运行 'isort backend' 来自动修复"
    FAILED=1
fi
echo ""

echo "[2/4] 运行 Black 检查代码格式..."
if ! black --check backend; then
    echo "[错误] Black 检查失败"
    echo "运行 'black backend' 来自动修复"
    FAILED=1
fi
echo ""

echo "[3/4] 运行 flake8 代码质量检查..."
if ! flake8 backend; then
    echo "[错误] Flake8 检查失败"
    FAILED=1
fi
echo ""

echo "[4/4] 显示代码统计..."
echo "Backend Python 文件数量:"
find backend -name "*.py" | wc -l
echo ""

if [ $FAILED -eq 1 ]; then
    echo "========================================"
    echo "代码质量检查失败！请修复上述问题。"
    echo "========================================"
    exit 1
else
    echo "========================================"
    echo "所有检查通过！✓"
    echo "========================================"
fi
