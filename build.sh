#!/bin/bash
# 群小二 - 打包工具

set -e

echo "========================================"
echo "  群小二 - 打包工具"
echo "========================================"
echo ""

echo "[1/3] 检查依赖..."
pip3 install pyinstaller nicegui openai flask pandas python-dotenv -q

echo "[2/3] 开始打包..."
pyinstaller build.spec --clean --noconfirm

echo "[3/3] 完成!"
echo ""

if [ -f "dist/群小二" ] || [ -f "dist/群小二.app" ]; then
    echo "✓ 打包成功!"
    echo "输出文件: dist/群小二"
    echo ""
    echo "使用方法:"
    echo "  1. 将 dist/群小二 复制到目标电脑"
    echo "  2. 首次运行会自动打开配置页面"
    echo "  3. 配置完成后即可使用"
else
    echo "✗ 打包失败，请查看错误信息"
fi
