"""Web管理后台 - Streamlit"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from config import config
from database import db


# 页面配置
st.set_page_config(
    page_title="群小二 - 管理后台",
    page_icon="🏘️",
    layout="wide"
)


def check_config():
    """检查配置是否完整"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

    if not os.path.exists(env_path):
        return False, "配置文件不存在"

    # 检查API Key
    if config.LLM_MODE == "api" and not config.API_KEY:
        return False, "API Key未配置"

    return True, "配置正常"


def save_config(updates):
    """保存配置到.env文件"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

    # 读取现有配置
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    # 更新配置
    new_lines = []
    updated_keys = set()

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            key = line.split('=')[0]
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line + '\n')
        else:
            new_lines.append(line + '\n')

    # 添加新配置
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")

    # 写入文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    # 重新加载配置
    from dotenv import load_dotenv
    load_dotenv(env_path, override=True)


def show_setup_guide():
    """显示首次配置引导"""
    st.title("🏘️ 群小二 - 首次配置向导")

    st.markdown("""
    ### 欢迎使用群小二！

    群小二是群众诉求智能分拣与预警系统，帮助网格员自动处理微信群消息。

    请按照以下步骤完成初始配置：
    """)

    # 步骤1：选择LLM模式
    st.header("步骤 1: 选择AI模型")
    st.markdown("选择一种方式来驱动AI分析功能：")

    col1, col2 = st.columns(2)

    with col1:
        st.info("**Ollama（本地部署）**\n- 完全免费\n- 数据不出内网\n- 需要下载模型（约4GB）\n- 需要GPU或8GB+内存")
        if st.button("选择 Ollama"):
            st.session_state['llm_mode'] = 'ollama'

    with col2:
        st.success("**API（云端调用）**\n- 开箱即用\n- 按量付费（很便宜）\n- 无需硬件\n- 响应更快")
        if st.button("选择 API"):
            st.session_state['llm_mode'] = 'api'

    # 步骤2：配置参数
    if 'llm_mode' in st.session_state:
        st.header("步骤 2: 配置参数")

        if st.session_state['llm_mode'] == 'ollama':
            show_ollama_config()
        else:
            show_api_config()


def show_ollama_config():
    """Ollama配置界面"""
    st.markdown("### Ollama 配置")

    st.markdown("""
    **安装Ollama：**
    ```bash
    # Linux/Mac
    curl -fsSL https://ollama.com/install.sh | sh

    # Windows
    # 访问 https://ollama.com 下载安装
    ```

    **下载模型：**
    ```bash
    ollama pull qwen2:7b
    ```
    """)

    with st.form("ollama_config"):
        base_url = st.text_input("Ollama地址", value="http://localhost:11434")
        model = st.selectbox("模型", ["qwen2:7b", "qwen2:1.5b", "llama3:8b", "llama3:1b"])

        if st.form_submit_button("保存并测试"):
            save_config({
                'LLM_MODE': 'ollama',
                'OLLAMA_BASE_URL': base_url,
                'OLLAMA_MODEL': model
            })
            st.success("配置已保存！正在测试连接...")

            # 测试连接
            from llm_service import llm_service
            if llm_service.test_connection():
                st.success("✓ 连接成功！")
                st.balloons()
                st.rerun()
            else:
                st.error("✗ 连接失败，请检查Ollama是否已启动")


def show_api_config():
    """API配置界面"""
    st.markdown("### API 配置")

    provider = st.selectbox("选择服务商", ["通义千问（阿里云）", "DeepSeek", "OpenAI"])

    if provider == "通义千问（阿里云）":
        st.markdown("""
        **获取API Key：**
        1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
        2. 注册/登录账号
        3. 进入"API-KEY管理"创建Key
        4. 新用户有免费额度
        """)
        default_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        default_model = "qwen-plus"
    elif provider == "DeepSeek":
        st.markdown("""
        **获取API Key：**
        1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
        2. 注册/登录账号
        3. 进入"API Keys"创建Key
        4. 新用户有免费额度
        """)
        default_url = "https://api.deepseek.com/v1"
        default_model = "deepseek-chat"
    else:
        st.markdown("""
        **获取API Key：**
        1. 访问 [OpenAI平台](https://platform.openai.com/)
        2. 注册/登录账号
        3. 进入"API Keys"创建Key
        """)
        default_url = "https://api.openai.com/v1"
        default_model = "gpt-4o-mini"

    with st.form("api_config"):
        api_key = st.text_input("API Key", type="password", placeholder="sk-...")
        api_url = st.text_input("API地址", value=default_url)
        model = st.text_input("模型名称", value=default_model)

        if st.form_submit_button("保存并测试"):
            if not api_key:
                st.error("请输入API Key")
            else:
                save_config({
                    'LLM_MODE': 'api',
                    'API_KEY': api_key,
                    'API_BASE_URL': api_url,
                    'API_MODEL': model
                })
                st.success("配置已保存！正在测试连接...")

                # 测试连接
                from llm_service import llm_service
                if llm_service.test_connection():
                    st.success("✓ 连接成功！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("✗ 连接失败，请检查API Key是否正确")


def show_main_app():
    """显示主应用"""
    st.title("🏘️ 群小二 - 群众诉求智能分拣与预警系统")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 系统状态")
        st.success(f"✓ 已配置")
        st.info(f"LLM模式: {config.LLM_MODE}")

        if config.LLM_MODE == "ollama":
            st.info(f"Ollama: {config.OLLAMA_BASE_URL}")
            st.info(f"模型: {config.OLLAMA_MODEL}")
        else:
            st.info(f"API: {config.API_BASE_URL}")
            st.info(f"模型: {config.API_MODEL}")

        st.divider()

        if st.button("测试LLM连接"):
            with st.spinner("测试中..."):
                from llm_service import llm_service
                if llm_service.test_connection():
                    st.success("✓ 连接成功")
                else:
                    st.error("✗ 连接失败")

        st.divider()

        if st.button("重新配置"):
            st.session_state.pop('configured', None)
            st.rerun()

        st.divider()

        # 手动测试
        st.header("📝 手动测试")
        test_msg = st.text_area("输入测试消息:")
        if st.button("分析") and test_msg:
            with st.spinner("分析中..."):
                from llm_service import llm_service
                result = llm_service.analyze_message(test_msg)
                st.json(result)

    # 主内容区
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 数据概览", "📨 消息记录", "🚨 预警管理", "📈 统计分析", "🔗 飞书接入"])

    with tab1:
        show_dashboard()

    with tab2:
        show_messages()

    with tab3:
        show_alerts()

    with tab4:
        show_stats()

    with tab5:
        show_feishu_config()


def show_dashboard():
    """数据概览"""
    stats = db.get_stats(days=7)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total = sum(stats['category_stats'].values())
        st.metric("本周消息总数", total)

    with col2:
        urgent = stats['category_stats'].get('urgent', 0)
        st.metric("紧急诉求", urgent, delta="需要处理" if urgent > 0 else None)

    with col3:
        alert_total = stats['alert_stats'].get('total', 0)
        st.metric("预警总数", alert_total)

    with col4:
        alert_handled = stats['alert_stats'].get('handled', 0)
        handle_rate = f"{alert_handled/alert_total*100:.1f}%" if alert_total > 0 else "0%"
        st.metric("处理率", handle_rate)

    # 分类分布
    st.subheader("消息分类分布")
    if stats['category_stats']:
        df = pd.DataFrame([
            {"分类": config.CATEGORIES.get(k, k), "数量": v}
            for k, v in stats['category_stats'].items()
        ])
        st.bar_chart(df.set_index("分类"))
    else:
        st.info("暂无数据")

    # 最近预警
    st.subheader("最近预警")
    alerts = db.get_alerts(is_handled=0)[:5]
    if alerts:
        for alert in alerts:
            with st.expander(f"[{alert['alert_level']}] {alert['alert_content'][:50]}..."):
                st.write(f"**消息内容**: {alert['content']}")
                st.write(f"**发送者**: {alert['sender_name']}")
                st.write(f"**时间**: {alert['created_at']}")
                if st.button("标记已处理", key=f"handle_{alert['id']}"):
                    db.handle_alert(alert['id'], "管理员")
                    st.rerun()
    else:
        st.info("暂无未处理预警")


def show_messages():
    """消息记录"""
    st.subheader("消息记录")

    # 筛选
    col1, col2 = st.columns(2)
    with col1:
        category_filter = st.selectbox(
            "按分类筛选",
            ["全部"] + list(config.CATEGORIES.values())
        )
    with col2:
        limit = st.number_input("显示条数", min_value=10, max_value=500, value=100)

    # 获取数据
    category = None
    if category_filter != "全部":
        category = [k for k, v in config.CATEGORIES.items() if v == category_filter][0]

    messages = db.get_messages(limit=limit, category=category)

    if messages:
        df = pd.DataFrame(messages)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at', ascending=False)

        # 显示表格
        display_df = df[['created_at', 'sender_name', 'content', 'category', 'summary', 'alert_level']].copy()
        display_df.columns = ['时间', '发送者', '内容', '分类', '摘要', '预警等级']
        display_df['分类'] = display_df['分类'].map(config.CATEGORIES)

        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("暂无消息记录")


def show_alerts():
    """预警管理"""
    st.subheader("预警管理")

    tab_unhandled, tab_all = st.tabs(["待处理", "全部"])

    with tab_unhandled:
        alerts = db.get_alerts(is_handled=0)
        if alerts:
            for alert in alerts:
                with st.expander(f"[{alert['alert_level']}] {alert['alert_content'][:50]}..."):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**消息内容**: {alert['content']}")
                        st.write(f"**发送者**: {alert['sender_name']}")
                        st.write(f"**时间**: {alert['created_at']}")
                        st.write(f"**预警等级**: {alert['alert_level']}")
                    with col2:
                        if st.button("处理", key=f"alert_{alert['id']}"):
                            db.handle_alert(alert['id'], "管理员")
                            st.rerun()
        else:
            st.success("暂无待处理预警")

    with tab_all:
        alerts = db.get_alerts()
        if alerts:
            df = pd.DataFrame(alerts)
            df['is_handled'] = df['is_handled'].map({0: '待处理', 1: '已处理'})
            display_df = df[['created_at', 'sender_name', 'alert_level', 'alert_content', 'is_handled', 'handled_by']].copy()
            display_df.columns = ['时间', '发送者', '等级', '内容', '状态', '处理人']
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("暂无预警记录")


def show_stats():
    """统计分析"""
    st.subheader("统计分析")

    days = st.slider("统计天数", 1, 30, 7)
    stats = db.get_stats(days=days)

    # 每日消息趋势
    st.subheader("每日消息趋势")
    if stats['daily_stats']:
        df = pd.DataFrame(stats['daily_stats'])
        st.line_chart(df.set_index("date"))
    else:
        st.info("暂无数据")

    # 分类统计
    st.subheader("分类统计")
    if stats['category_stats']:
        col1, col2 = st.columns(2)
        with col1:
            df = pd.DataFrame([
                {"分类": config.CATEGORIES.get(k, k), "数量": v}
                for k, v in stats['category_stats'].items()
            ])
            st.bar_chart(df.set_index("分类"))
        with col2:
            st.dataframe(df, use_container_width=True)


def show_feishu_config():
    """飞书接入配置"""
    st.header("飞书机器人接入")

    st.markdown("配置飞书应用凭证，让机器人自动监听群消息并智能分析。")

    # 当前状态
    feishu_configured = bool(config.FEISHU_APP_ID and config.FEISHU_APP_SECRET)

    if feishu_configured:
        st.success("✅ 飞书已配置")
    else:
        st.warning("⚠️ 飞书未配置")

    st.divider()

    # 步骤引导
    st.subheader("步骤 1: 创建飞书应用")
    st.markdown("""
    1. 打开 [飞书开放平台](https://open.feishu.cn/app)
    2. 点击「创建企业自建应用」
    3. 填写应用名称（如：群小二）
    4. 创建完成后，进入应用详情页
    """)

    st.subheader("步骤 2: 开启机器人能力")
    st.markdown("""
    1. 在应用详情页，点击「添加应用能力」
    2. 选择「机器人」
    3. 进入「事件订阅」页面
    4. 添加事件：`im.message.receive_v1`（接收消息）
    """)

    st.subheader("步骤 3: 填入凭证")

    with st.form("feishu_config"):
        app_id = st.text_input("App ID", value=config.FEISHU_APP_ID or "", placeholder="cli_xxxxxxxxxx")
        app_secret = st.text_input("App Secret", value=config.FEISHU_APP_SECRET or "", type="password")
        verification_token = st.text_input("Verification Token", value=config.FEISHU_VERIFICATION_TOKEN or "", help="可选，用于验证请求来源")
        encrypt_key = st.text_input("Encrypt Key", value=config.FEISHU_ENCRYPT_KEY or "", type="password", help="可选，用于加密事件回调")

        if st.form_submit_button("保存配置"):
            if not app_id or not app_secret:
                st.error("请填写 App ID 和 App Secret")
            else:
                save_config({
                    'FEISHU_APP_ID': app_id,
                    'FEISHU_APP_SECRET': app_secret,
                    'FEISHU_VERIFICATION_TOKEN': verification_token,
                    'FEISHU_ENCRYPT_KEY': encrypt_key
                })
                st.success("飞书配置已保存！")
                st.rerun()

    st.divider()

    st.subheader("步骤 4: 配置回调地址")
    st.markdown("""
    回到飞书开放平台，进入「事件订阅」页面，填写：

    **请求地址**: `http://你的服务器IP:8000/webhook/event`

    > 如果是本地测试，需要使用内网穿透工具（如 ngrok）获取公网地址
    """)

    st.divider()

    st.subheader("步骤 5: 启动机器人")
    st.markdown("配置完成后，在终端运行以下命令启动机器人：")
    st.code("cd src && python main.py bot", language="bash")


def main():
    """主函数"""
    # 检查配置
    is_configured, msg = check_config()

    if not is_configured:
        show_setup_guide()
    else:
        show_main_app()


if __name__ == "__main__":
    main()
