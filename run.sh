#!/bin/bash
# 群小二 - 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        print_error "未找到Python，请先安装Python 3.10+"
        exit 1
    fi

    VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
    print_info "Python版本: $VERSION"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    $PYTHON -m pip install -r requirements.txt -q
    print_info "依赖检查完成"
}

# 检查配置
check_config() {
    if [ ! -f .env ]; then
        print_warn ".env文件不存在，正在从示例创建..."
        cp .env.example .env
        print_warn "请编辑 .env 文件配置飞书和LLM参数"
        print_warn "配置完成后重新运行此脚本"
        exit 1
    fi
    print_info "配置文件检查完成"
}

# 测试LLM连接
test_llm() {
    print_info "测试LLM连接..."
    $PYTHON src/main.py test
}

# 启动服务
start_bot() {
    print_info "启动飞书机器人服务..."
    $PYTHON src/main.py bot
}

start_web() {
    print_info "启动Web管理后台..."
    $PYTHON src/main.py web
}

start_all() {
    print_info "启动全部服务..."
    $PYTHON src/main.py all
}

# 显示帮助
show_help() {
    echo "群小二 - 群众诉求智能分拣与预警系统"
    echo ""
    echo "用法: ./run.sh [命令]"
    echo ""
    echo "命令:"
    echo "  check     检查环境和配置"
    echo "  test      测试LLM连接"
    echo "  bot       启动飞书机器人服务"
    echo "  web       启动Web管理后台"
    echo "  all       启动全部服务（默认）"
    echo "  help      显示此帮助信息"
}

# 主流程
main() {
    check_python

    case "${1:-all}" in
        check)
            check_dependencies
            check_config
            ;;
        test)
            check_dependencies
            check_config
            test_llm
            ;;
        bot)
            check_dependencies
            check_config
            start_bot
            ;;
        web)
            check_dependencies
            check_config
            start_web
            ;;
        all)
            check_dependencies
            check_config
            start_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
