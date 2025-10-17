#!/bin/bash
# 自动格式化代码脚本

set -e

echo "========================================"
echo "自动格式化代码"
echo "========================================"
echo ""

echo "[1/2] 运行 isort 排序导入语句..."
isort backend
echo "✓ isort 完成"
echo ""

echo "[2/2] 运行 Black 格式化代码..."
black backend
echo "✓ Black 完成"
echo ""

echo "========================================"
echo "代码格式化完成！"
echo "========================================"
echo ""
echo "现在运行质量检查..."
./quality_check.sh
