"""主程序入口"""
import sys
import os
import argparse
from config import config


def run_bot():
    """启动飞书机器人服务"""
    print(f"启动群小二飞书机器人服务...")
    print(f"LLM模式: {config.LLM_MODE}")
    print(f"机器人模式: {config.BOT_MODE}")

    if config.LLM_MODE == "ollama":
        print(f"Ollama地址: {config.OLLAMA_BASE_URL}")
        print(f"模型: {config.OLLAMA_MODEL}")
    else:
        print(f"API地址: {config.API_BASE_URL}")
        print(f"模型: {config.API_MODEL}")

    if config.BOT_MODE == "sdk":
        print("使用SDK长连接模式（无需公网URL）")
        from feishu_bot_sdk import bot_sdk
        try:
            bot_sdk.start()
        except KeyboardInterrupt:
            print("\n机器人已停止")
            bot_sdk.stop()
    else:
        print(f"使用Webhook模式，监听地址: {config.HOST}:{config.PORT}")
        from feishu_bot import app
        app.run(host=config.HOST, port=config.PORT, debug=False)


def run_desktop():
    """启动桌面管理后台"""
    print(f"启动群小二桌面管理后台...")
    from desktop_gui import main
    main()


def run_web():
    """启动Web管理后台"""
    print(f"启动群小二Web管理后台...")
    print(f"访问地址: http://localhost:{config.WEB_PORT}")

    os.system(f"streamlit run web_admin.py --server.port {config.WEB_PORT}")


def run_test():
    """运行测试"""
    print("测试LLM连接...")
    from llm_service import llm_service

    if llm_service.test_connection():
        print("✓ LLM连接成功")

        # 测试消息分析
        test_messages = [
            "我们楼的电梯又坏了，老人上下楼怎么办啊",
            "今天天气真好，大家早上好",
            "隔壁装修噪音太大了，周末都不休息",
            "小区门口的路灯坏了好几天了，晚上黑漆漆的"
        ]

        print("\n测试消息分析:")
        for msg in test_messages:
            result = llm_service.analyze_message(msg)
            print(f"\n消息: {msg}")
            print(f"分类: {result.get('category')}")
            print(f"摘要: {result.get('summary')}")
            print(f"需要预警: {result.get('need_alert')}")
    else:
        print("✗ LLM连接失败")
        print("请检查配置:")
        if config.LLM_MODE == "ollama":
            print(f"  - Ollama地址: {config.OLLAMA_BASE_URL}")
            print(f"  - 模型: {config.OLLAMA_MODEL}")
            print("  - 确保Ollama已启动: ollama serve")
        else:
            print(f"  - API Key: {'已配置' if config.API_KEY else '未配置'}")
            print(f"  - API地址: {config.API_BASE_URL}")


def main():
    parser = argparse.ArgumentParser(description="群小二 - 群众诉求智能分拣与预警系统")
    parser.add_argument("command", choices=["bot", "desktop", "web", "test", "all"],
                        help="运行命令: bot=飞书机器人, desktop=桌面管理后台, web=Web管理后台, test=测试, all=全部")

    args = parser.parse_args()

    if args.command == "bot":
        run_bot()
    elif args.command == "desktop":
        run_desktop()
    elif args.command == "web":
        run_web()
    elif args.command == "test":
        run_test()
    elif args.command == "all":
        import threading
        # 启动机器人服务
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        # 启动桌面管理后台
        run_desktop()


if __name__ == "__main__":
    main()
