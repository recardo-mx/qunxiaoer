"""群小二 - 管理后台"""
import sys
import os
import subprocess
sys.path.insert(0, os.path.dirname(__file__))

from nicegui import ui
from config import config
from database import db

# 主题色
PRIMARY = '#4F46E5'
PRIMARY_LIGHT = '#EEF2FF'
PRIMARY_DARK = '#3730A3'
SUCCESS = '#059669'
SUCCESS_LIGHT = '#D1FAE5'
WARNING = '#D97706'
WARNING_LIGHT = '#FEF3C7'
DANGER = '#DC2626'
DANGER_LIGHT = '#FEE2E2'
GRAY_50 = '#F9FAFB'
GRAY_100 = '#F3F4F6'
GRAY_200 = '#E5E7EB'
GRAY_400 = '#9CA3AF'
GRAY_500 = '#6B7280'
GRAY_600 = '#4B5563'
GRAY_700 = '#374151'
GRAY_800 = '#1F2937'
GRAY_900 = '#111827'

app_state = {
    'configured': False,
    'llm_mode': None,
    'bot_process': None,
    'bot_running': False
}


def check_config():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_path):
        return False
    if config.LLM_MODE == "api" and not config.API_KEY:
        return False
    return True


def save_config(updates):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

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

    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")

    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    from dotenv import load_dotenv
    load_dotenv(env_path, override=True)

    for key, value in updates.items():
        if hasattr(config, key):
            if key in ('PORT', 'WEB_PORT'):
                setattr(config, key, int(value))
            else:
                setattr(config, key, value)


def test_llm_connection():
    try:
        from llm_service import llm_service
        return llm_service.test_connection()
    except Exception:
        return False


def analyze_message(message):
    try:
        from llm_service import llm_service
        return llm_service.analyze_message(message)
    except Exception as e:
        return {
            "category": "other",
            "summary": message[:50],
            "need_alert": False,
            "alert_level": "low",
            "suggested_action": str(e)
        }


def inject_styles():
    ui.add_head_html(f'''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/icon?family=Material+Icons');

        * {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px;
            line-height: 1.5;
        }}

        h1 {{ font-size: 24px; font-weight: 700; color: {GRAY_900}; }}
        h2 {{ font-size: 20px; font-weight: 600; color: {GRAY_800}; }}
        h3 {{ font-size: 16px; font-weight: 600; color: {GRAY_700}; }}

        .q-btn {{ font-weight: 500; letter-spacing: 0; text-transform: none; }}

        .app-header {{
            background: {PRIMARY};
            color: white;
        }}

        .sidebar {{
            background: white;
            border-right: 1px solid {GRAY_200};
        }}

        .sidebar-item {{
            padding: 10px 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s ease;
            color: {GRAY_600};
            font-weight: 500;
            font-size: 14px;
        }}
        .sidebar-item:hover {{
            background: {GRAY_100};
            color: {GRAY_800};
        }}
        .sidebar-item.active {{
            background: {PRIMARY_LIGHT};
            color: {PRIMARY};
        }}

        .stat-card {{
            background: white;
            border-radius: 12px;
            border: 1px solid {GRAY_200};
            transition: box-shadow 0.2s ease;
        }}
        .stat-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        }}

        .content-card {{
            background: white;
            border-radius: 12px;
            border: 1px solid {GRAY_200};
        }}

        .alert-item {{
            border-left: 4px solid;
            border-radius: 8px;
            transition: background 0.15s ease;
        }}
        .alert-item:hover {{
            background: {GRAY_50};
        }}
        .alert-high {{ border-color: {DANGER}; }}
        .alert-medium {{ border-color: {WARNING}; }}
        .alert-low {{ border-color: {PRIMARY}; }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }}
        .status-online {{ background: {SUCCESS_LIGHT}; color: {SUCCESS}; }}
        .status-offline {{ background: {DANGER_LIGHT}; color: {DANGER}; }}

        .setup-option {{
            border: 2px solid {GRAY_200};
            border-radius: 12px;
            padding: 24px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .setup-option:hover {{
            border-color: {PRIMARY};
            background: {PRIMARY_LIGHT};
        }}
        .setup-option.selected {{
            border-color: {PRIMARY};
            background: {PRIMARY_LIGHT};
        }}

        .empty-state {{
            text-align: center;
            padding: 48px 24px;
            color: {GRAY_400};
        }}

        .section-title {{
            font-size: 16px;
            font-weight: 600;
            color: {GRAY_800};
            margin-bottom: 16px;
        }}

        .btn-primary {{
            background: {PRIMARY} !important;
            color: white !important;
        }}
        .btn-success {{
            background: {SUCCESS} !important;
            color: white !important;
        }}
        .text-xs {{ font-size: 12px; }}
        .text-muted {{ color: {GRAY_500}; }}
        .text-primary {{ color: {PRIMARY}; }}
        .text-success {{ color: {SUCCESS}; }}
        .text-warning {{ color: {WARNING}; }}
        .text-danger {{ color: {DANGER}; }}

        .bg-main {{ background: {GRAY_50}; }}
    </style>
    ''')


@ui.page('/')
def main_page():
    inject_styles()
    if not check_config():
        show_setup_page()
    else:
        show_dashboard()


def show_setup_page():
    with ui.column().classes('w-full min-h-screen items-center justify-center').style(f'background: {GRAY_50}'):
        with ui.card().classes('w-full max-w-2xl p-8 shadow-lg').style('border-radius: 16px; border: none;'):
            with ui.column().classes('items-center mb-8'):
                ui.label('群小二').style(f'font-size: 28px; font-weight: 700; color: {PRIMARY};')
                ui.label('群众诉求智能分拣与预警系统').style(f'font-size: 15px; color: {GRAY_500}; margin-top: 4px;')

            ui.linear_progress(value=0.33, show_value=False).classes('w-full mb-8').props(f'color={PRIMARY}')

            ui.label('选择 AI 模型').style(f'font-size: 18px; font-weight: 600; color: {GRAY_800};')
            ui.label('选择一种方式来驱动消息分析功能').style(f'font-size: 14px; color: {GRAY_500}; margin-bottom: 24px;')

            with ui.row().classes('w-full gap-4'):
                with ui.card().classes('flex-1 setup-option').style('border-radius: 12px;') as ollama_card:
                    with ui.column().classes('items-center gap-2'):
                        ui.label('本地部署').style(f'font-size: 16px; font-weight: 600; color: {GRAY_800};')
                        ui.label('Ollama').style(f'font-size: 13px; color: {GRAY_500}; margin-bottom: 12px;')
                        with ui.column().classes('gap-1').style(f'font-size: 13px; color: {GRAY_600};'):
                            ui.label('完全免费')
                            ui.label('数据不出内网')
                            ui.label('需要 8GB+ 内存')

                with ui.card().classes('flex-1 setup-option').style('border-radius: 12px;') as api_card:
                    with ui.column().classes('items-center gap-2'):
                        ui.label('云端调用').style(f'font-size: 16px; font-weight: 600; color: {GRAY_800};')
                        ui.label('API').style(f'font-size: 13px; color: {GRAY_500}; margin-bottom: 12px;')
                        with ui.column().classes('gap-1').style(f'font-size: 13px; color: {GRAY_600};'):
                            ui.label('开箱即用')
                            ui.label('响应更快')
                            ui.label('按量付费')

            form_container = ui.column().classes('w-full mt-4')

        def select_ollama():
            ollama_card.classes(remove='setup-option', add='selected')
            api_card.classes(remove='selected', add='setup-option')
            form_container.clear()
            show_ollama_form(form_container)

        def select_api():
            api_card.classes(remove='setup-option', add='selected')
            ollama_card.classes(remove='selected', add='setup-option')
            form_container.clear()
            show_api_form(form_container)

        ollama_card.on('click', select_ollama)
        api_card.on('click', select_api)


def show_ollama_form(container):
    with container:
        with ui.card().classes('w-full p-6').style(f'background: {GRAY_50}; border-radius: 12px; border: 1px solid {GRAY_200};'):
            ui.label('配置 Ollama').style(f'font-size: 16px; font-weight: 600; color: {GRAY_800}; margin-bottom: 16px;')

            with ui.stepper().classes('w-full') as stepper:
                with ui.step('安装 Ollama'):
                    ui.markdown('''
                    1. 访问 [ollama.com](https://ollama.com) 下载安装
                    2. 或使用命令：
                    ```bash
                    curl -fsSL https://ollama.com/install.sh | sh
                    ```
                    ''')
                    with ui.stepper_navigation():
                        ui.button('下一步', on_click=stepper.next).props(f'color={PRIMARY}').classes('btn-primary')

                with ui.step('下载模型'):
                    ui.label('打开终端，运行以下命令下载模型：').style(f'font-size: 14px; color: {GRAY_600};')
                    ui.code('ollama pull qwen2:7b', language='bash').classes('w-full')
                    ui.label('下载约需几分钟，取决于网速').style(f'font-size: 12px; color: {GRAY_500}; margin-top: 8px;')
                    with ui.stepper_navigation():
                        ui.button('上一步', on_click=stepper.previous).props('flat')
                        ui.button('下一步', on_click=stepper.next).props(f'color={PRIMARY}').classes('btn-primary')

                with ui.step('测试连接'):
                    base_url = ui.input('Ollama 地址', value='http://localhost:11434').classes('w-full')
                    model = ui.select(
                        ['qwen2:7b', 'qwen2:1.5b', 'qwen2:0.5b'],
                        value='qwen2:7b',
                        label='选择模型'
                    ).classes('w-full')

                    async def save_and_test():
                        save_config({
                            'LLM_MODE': 'ollama',
                            'OLLAMA_BASE_URL': base_url.value,
                            'OLLAMA_MODEL': model.value
                        })
                        ui.notify('正在测试连接...', type='info')
                        if test_llm_connection():
                            ui.notify('连接成功', type='positive')
                            ui.navigate.to('/')
                        else:
                            ui.notify('连接失败，请检查 Ollama 是否已启动', type='negative')

                    with ui.stepper_navigation():
                        ui.button('上一步', on_click=stepper.previous).props('flat')
                        ui.button('保存并测试', on_click=save_and_test).props(f'color={PRIMARY}').classes('btn-primary')


def show_api_form(container):
    with container:
        with ui.card().classes('w-full p-6').style(f'background: {GRAY_50}; border-radius: 12px; border: 1px solid {GRAY_200};'):
            ui.label('配置 API').style(f'font-size: 16px; font-weight: 600; color: {GRAY_800}; margin-bottom: 16px;')

            providers = {
                '通义千问（阿里云）': {
                    'help': '访问 [阿里云百炼平台](https://bailian.console.aliyun.com/) 获取 API Key',
                    'url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                    'model': 'qwen-plus',
                },
                'DeepSeek': {
                    'help': '访问 [DeepSeek 开放平台](https://platform.deepseek.com/) 获取 API Key',
                    'url': 'https://api.deepseek.com/v1',
                    'model': 'deepseek-chat',
                },
                'OpenAI': {
                    'help': '访问 [OpenAI 平台](https://platform.openai.com/) 获取 API Key',
                    'url': 'https://api.openai.com/v1',
                    'model': 'gpt-4o-mini',
                }
            }

            provider = ui.select(
                list(providers.keys()),
                value='通义千问（阿里云）',
                label='服务商'
            ).classes('w-full')

            help_text = ui.markdown(providers['通义千问（阿里云）']['help']).style(f'font-size: 13px; color: {GRAY_500}; margin: 12px 0;')

            api_key = ui.input('API Key', password=True, placeholder='sk-...').classes('w-full')
            api_url = ui.input('API 地址', value=providers['通义千问（阿里云）']['url']).classes('w-full')
            model = ui.input('模型名称', value=providers['通义千问（阿里云）']['model']).classes('w-full')

            def on_provider_change():
                p = providers[provider.value]
                help_text.content = p['help']
                api_url.value = p['url']
                model.value = p['model']

            provider.on('change', on_provider_change)

            async def save_and_test():
                if not api_key.value:
                    ui.notify('请输入 API Key', type='negative')
                    return
                save_config({
                    'LLM_MODE': 'api',
                    'API_KEY': api_key.value,
                    'API_BASE_URL': api_url.value,
                    'API_MODEL': model.value
                })
                ui.notify('正在测试连接...', type='info')
                if test_llm_connection():
                    ui.notify('连接成功', type='positive')
                    ui.navigate.to('/')
                else:
                    ui.notify('连接失败，请检查 API Key 是否正确', type='negative')

            ui.button('保存并测试', on_click=save_and_test).classes('w-full mt-4 btn-primary').props(f'color={PRIMARY} size=lg')


def show_dashboard():
    inject_styles()

    # 顶部导航
    with ui.header().classes('app-header').style('height: 56px;'):
        with ui.row().classes('w-full items-center px-6'):
            ui.label('群小二').style('font-size: 18px; font-weight: 700; letter-spacing: 0.5px;')
            ui.space()
            feishu_ok = bool(config.FEISHU_APP_ID and config.FEISHU_APP_SECRET and 'your-' not in config.FEISHU_APP_ID)
            if app_state['bot_running']:
                ui.label('机器人运行中').classes('status-badge status-online')
            elif feishu_ok:
                ui.label('飞书已配置').style(f'font-size: 12px; font-weight: 500; color: {WARNING}; background: {WARNING_LIGHT}; padding: 2px 10px; border-radius: 12px;')
            else:
                ui.label('飞书未配置').classes('status-badge status-offline')
            ui.button(icon='settings', on_click=lambda: ui.navigate.to('/')).props('flat color=white').style('margin-left: 12px;')

    # 侧边栏
    with ui.left_drawer().classes('sidebar').style('width: 200px; padding: 16px 12px;'):
        ui.label('导航').style(f'font-size: 11px; font-weight: 600; color: {GRAY_400}; text-transform: uppercase; letter-spacing: 1px; padding: 0 12px; margin-bottom: 8px;')

        menu_items = [
            ('overview', '数据概览'),
            ('messages', '消息记录'),
            ('alerts', '预警管理'),
            ('stats', '统计分析'),
            ('feishu', '飞书接入'),
            ('test', '功能测试'),
        ]

        menu_buttons = {}

        for tab_id, label in menu_items:
            btn = ui.label(label).classes('sidebar-item')
            btn.on('click', lambda t=tab_id: switch_tab(t))
            menu_buttons[tab_id] = btn

        ui.separator().style(f'margin: 16px 0; border-color: {GRAY_200};')

        ui.label('系统').style(f'font-size: 11px; font-weight: 600; color: {GRAY_400}; text-transform: uppercase; letter-spacing: 1px; padding: 0 12px; margin-bottom: 8px;')

        with ui.card().classes('w-full').style(f'padding: 12px; background: {GRAY_50}; border-radius: 8px; border: 1px solid {GRAY_200};'):
            if config.LLM_MODE == 'ollama':
                ui.label('本地模型').style(f'font-size: 12px; color: {GRAY_500};')
                ui.label(config.OLLAMA_MODEL).style(f'font-size: 13px; font-weight: 500; color: {GRAY_700};')
            else:
                ui.label('云端 API').style(f'font-size: 12px; color: {GRAY_500};')
                ui.label(config.API_MODEL).style(f'font-size: 13px; font-weight: 500; color: {GRAY_700};')

    def switch_tab(tab_id):
        tabs.set_value(tab_id)
        for tid, btn in menu_buttons.items():
            if tid == tab_id:
                btn.classes(remove='')
                btn.classes(add='active')
            else:
                btn.classes(remove='active')

    # 主内容区
    with ui.column().classes('w-full bg-main').style('min-height: calc(100vh - 56px); padding: 24px;'):
        tabs = ui.tabs().classes('hidden')

        with tabs:
            for tab_id in ['overview', 'messages', 'alerts', 'stats', 'feishu', 'test']:
                ui.tab(tab_id)

        tab_panels = {
            'overview': show_overview_tab,
            'messages': show_messages_tab,
            'alerts': show_alerts_tab,
            'stats': show_stats_tab,
            'feishu': show_feishu_tab,
            'test': show_test_tab,
        }

        content_area = ui.column().classes('w-full')

        def render_tab(tab_id):
            content_area.clear()
            with content_area:
                tab_panels[tab_id]()

        tabs.on_value_change(lambda e: render_tab(e.value))
        render_tab('overview')
        menu_buttons['overview'].classes(add='active')


def show_overview_tab():
    # 时间范围选择
    time_range = ui.select(['本周', '本月', '全部'], value='本周', label='时间范围').classes('w-32 mb-4')
    
    def get_days():
        return {'本周': 7, '本月': 30, '全部': 365}[time_range.value]

    def refresh_overview():
        stats = db.get_stats(days=get_days())
        alert_total = stats['alert_stats'].get('total', 0)
        alert_handled = stats['alert_stats'].get('handled', 0)
        handle_rate = f"{alert_handled / alert_total * 100:.0f}%" if alert_total > 0 else '0%'
        total_msgs = sum(stats['category_stats'].values())
        urgent_count = stats['category_stats'].get('urgent', 0)

        # KPI 卡片
        overview_content.clear()
        with overview_content:
            with ui.row().classes('w-full gap-4 mb-6'):
                for title, value, subtitle, color in [
                    (f'{time_range.value}消息', str(total_msgs), '全部消息', PRIMARY),
                    ('紧急诉求', str(urgent_count), '需要立即处理', DANGER),
                    ('预警总数', str(alert_total), '待处理预警', WARNING),
                    ('处理率', handle_rate, '已处理占比', SUCCESS),
                ]:
                    with ui.card().classes('stat-card flex-1 p-5'):
                        ui.label(title).style(f'font-size: 13px; color: {GRAY_500}; font-weight: 500;')
                        ui.label(value).style(f'font-size: 28px; font-weight: 700; color: {color}; margin: 8px 0 4px;')
                        ui.label(subtitle).style(f'font-size: 12px; color: {GRAY_400};')

            with ui.row().classes('w-full gap-6'):
                # 分类饼图
                with ui.card().classes('content-card flex-1 p-6'):
                    ui.label('消息分类分布').classes('section-title')
                    if stats['category_stats']:
                        pie_data = [{'name': config.CATEGORIES.get(k, k), 'value': v} for k, v in stats['category_stats'].items()]
                        ui.echart({
                            'tooltip': {'trigger': 'item'},
                            'legend': {'orient': 'vertical', 'left': 'left', 'textStyle': {'fontSize': 12}},
                            'series': [{
                                'type': 'pie', 'radius': ['40%', '70%'], 'center': ['55%', '50%'],
                                'data': pie_data,
                                'label': {'show': True, 'formatter': '{b}\n{d}%'},
                                'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowOffsetX': 0, 'shadowColor': 'rgba(0,0,0,0.5)'}}
                            }]
                        }).classes('w-full').style('height: 300px')
                    else:
                        with ui.column().classes('empty-state'):
                            ui.label('暂无数据').style(f'font-size: 14px; color: {GRAY_400};')

                # 最近预警
                with ui.card().classes('content-card flex-1 p-6'):
                    ui.label('最近预警').classes('section-title')
                    alerts = db.get_alerts(is_handled=0)[:5]
                    if alerts:
                        for alert in alerts:
                            level = alert['alert_level'] or 'low'
                            level_class = f'alert-{level}'
                            level_colors = {'high': DANGER, 'medium': WARNING, 'low': PRIMARY}
                            with ui.card().classes(f'alert-item {level_class} p-3 mb-2').style(f'border-radius: 8px; border: none; background: {GRAY_50};'):
                                with ui.row().classes('items-center justify-between'):
                                    with ui.column().classes('flex-1'):
                                        badge_color = level_colors.get(level, GRAY_500)
                                        ui.label(alert['alert_content'][:50]).style(f'font-size: 13px; font-weight: 500; color: {GRAY_800};')
                                        ui.label(f"{alert['sender_name']}  {alert['created_at'][:16]}").style(f'font-size: 12px; color: {GRAY_400};')
                                    ui.button('处理', on_click=lambda a=alert: handle_alert(a['id'])).props('size=sm flat').style(f'color: {PRIMARY};')
                    else:
                        with ui.column().classes('empty-state'):
                            ui.label('暂无待处理预警').style(f'font-size: 14px; color: {GRAY_400};')

    time_range.on('change', lambda _: refresh_overview())
    overview_content = ui.column().classes('w-full')
    refresh_overview()


def handle_alert(alert_id):
    db.handle_alert(alert_id, '管理员')
    ui.notify('已标记为已处理', type='positive')
    ui.navigate.to('/')


def show_messages_tab():
    with ui.card().classes('content-card p-6'):
        ui.label('消息记录').style(f'font-size: 16px; font-weight: 600; color: {GRAY_800}; margin-bottom: 16px;')
        
        # 搜索 + 筛选行
        with ui.row().classes('w-full gap-3 mb-4'):
            search_input = ui.input('关键词搜索', placeholder='搜索消息内容...').classes('flex-1').props('clearable')
            cat_select = ui.select(['全部'] + list(config.CATEGORIES.values()), value='全部', label='分类').classes('w-36')
            ui.button('搜索', icon='search', on_click=lambda: refresh_messages()).props(f'color={PRIMARY}')

        # 表格容器
        table_container = ui.column().classes('w-full')
        pagination_row = ui.row().classes('w-full items-center justify-center gap-2 mt-4')
        page_label = ui.label('').style(f'font-size: 13px; color: {GRAY_500};')

        current_page = {'value': 1}
        page_size = 15

        def refresh_messages():
            keyword = search_input.value.strip() or None
            category = cat_select.value
            page = current_page['value']

            result = db.search_messages(keyword=keyword, category=category, page=page, page_size=page_size)
            
            table_container.clear()
            with table_container:
                if result['items']:
                    for msg in result['items']:
                        cat_label = config.CATEGORIES.get(msg['category'], msg['category'])
                        level = msg['alert_level'] or ''
                        level_colors = {'high': DANGER, 'medium': WARNING, 'low': PRIMARY}
                        level_labels = {'high': '紧急', 'medium': '警告', 'low': '提示'}
                        time_str = msg['created_at'][:16] if msg['created_at'] else '-'
                        sender_str = msg['sender_name'] or '-'
                        
                        with ui.expansion(f'{time_str} | {sender_str} | {cat_label}', icon='chat').classes('w-full mb-1').style(f'border: 1px solid {GRAY_200}; border-radius: 8px;'):
                            with ui.column().classes('w-full gap-2 p-2'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label('内容:').style(f'font-size: 12px; font-weight: 600; color: {GRAY_500};')
                                    if level:
                                        lc = level_colors.get(level, GRAY_500)
                                        ll = level_labels.get(level, level)
                                        ui.label(ll).style(f'font-size: 11px; color: {lc}; background: {lc}15; padding: 1px 8px; border-radius: 8px;')
                                ui.label((msg['content'] or '-')).style(f'font-size: 13px; color: {GRAY_800}; white-space: pre-wrap; line-height: 1.6;')
                                if msg.get('summary'):
                                    with ui.row().classes('items-start gap-2'):
                                        ui.label('摘要:').style(f'font-size: 12px; font-weight: 600; color: {GRAY_500};')
                                        ui.label(msg['summary']).style(f'font-size: 12px; color: {GRAY_600};')
                else:
                    with ui.column().classes('empty-state'):
                        ui.label('未找到匹配的消息').style(f'font-size: 14px; color: {GRAY_400};')

            # 分页
            page_label.set_text(f'共 {result["total"]} 条  |  第 {page}/{result["total_pages"]} 页')
            pagination_row.clear()
            with pagination_row:
                ui.button(icon='first_page', on_click=lambda: go_page(1)).props('flat round dense').bind_enabled_from(current_page, 'value', lambda v: v > 1)
                ui.button(icon='chevron_left', on_click=lambda: go_page(page - 1)).props('flat round dense').bind_enabled_from(current_page, 'value', lambda v: v > 1)
                ui.label(f'{page}/{result["total_pages"]}').style(f'font-size: 13px; color: {GRAY_600}; min-width: 60px; text-align: center;')
                ui.button(icon='chevron_right', on_click=lambda: go_page(page + 1)).props('flat round dense').bind_enabled_from(current_page, 'value', lambda v: v < result['total_pages'])
                ui.button(icon='last_page', on_click=lambda: go_page(result['total_pages'])).props('flat round dense').bind_enabled_from(current_page, 'value', lambda v: v < result['total_pages'])

        def go_page(p):
            current_page['value'] = max(1, min(p, 999))
            refresh_messages()

        refresh_messages()


def show_alerts_tab():
    with ui.card().classes('content-card p-6'):
        ui.label('预警管理').style(f'font-size: 16px; font-weight: 600; color: {GRAY_800}; margin-bottom: 16px;')

        # 状态筛选标签
        filter_state = {'value': 'pending'}
        
        with ui.row().classes('gap-2 mb-6'):
            for state_id, label in [('all', '全部'), ('pending', '未处理'), ('handled', '已处理')]:
                btn = ui.button(label, on_click=lambda s=state_id: switch_filter(s))
                if state_id == 'pending':
                    btn.props('unelevated').style(f'background: {PRIMARY} !important; color: white !important;')
                    btn.classes('text-xs')
                else:
                    btn.props('outline').style(f'color: {GRAY_600}; border-color: {GRAY_300};')
                    btn.classes('text-xs')
                filter_state[f'btn_{state_id}'] = btn

        alerts_container = ui.column().classes('w-full')

        def switch_filter(state):
            filter_state['value'] = state
            for sid in ['all', 'pending', 'handled']:
                btn = filter_state.get(f'btn_{sid}')
                if btn:
                    if sid == state:
                        btn.props('unelevated').style(f'background: {PRIMARY} !important; color: white !important;')
                    else:
                        btn.props('outline').style(f'color: {GRAY_600}; border-color: {GRAY_300};')
            refresh_alerts()

        def refresh_alerts():
            state = filter_state['value']
            if state == 'all':
                alerts = db.get_alerts()
            elif state == 'handled':
                alerts = db.get_alerts(is_handled=1)
            else:
                alerts = db.get_alerts(is_handled=0)

            alerts_container.clear()
            with alerts_container:
                if alerts:
                    for alert in alerts:
                        level = alert['alert_level'] or 'low'
                        level_colors = {'high': DANGER, 'medium': WARNING, 'low': PRIMARY}
                        level_labels = {'high': '紧急', 'medium': '警告', 'low': '提示'}
                        color = level_colors.get(level, GRAY_500)
                        label_text = level_labels.get(level, '未知')

                        with ui.card().classes(f'alert-item alert-{level} p-4 mb-3').style(f'border-radius: 8px; border: none; background: white;'):
                            with ui.row().classes('items-center justify-between'):
                                with ui.column().classes('flex-1'):
                                    with ui.row().classes('items-center gap-2 mb-2'):
                                        ui.label(label_text).style(f'font-size: 12px; font-weight: 600; color: white; background: {color}; padding: 2px 10px; border-radius: 12px;')
                                        if alert['is_handled']:
                                            ui.label('已处理').style(f'font-size: 12px; color: {SUCCESS}; background: {SUCCESS_LIGHT}; padding: 2px 10px; border-radius: 12px;')
                                        ui.label(alert['alert_content']).style(f'font-size: 14px; font-weight: 600; color: {GRAY_800};')
                                    ui.label((alert.get('content') or '')[:100]).style(f'font-size: 13px; color: {GRAY_600}; margin-bottom: 4px;')
                                    ui.label(f"{alert.get('sender_name', '-')}  {alert['created_at'][:16]}").style(f'font-size: 12px; color: {GRAY_400};')
                                if not alert['is_handled']:
                                    with ui.row().classes('gap-2'):
                                        ui.button('详情', on_click=lambda a=alert: show_alert_detail(a)).props('flat').style(f'color: {PRIMARY};')
                                        ui.button('标记处理', on_click=lambda a=alert: handle_alert(a['id'])).props('unelevated').style(f'background: {color} !important; color: white !important;')
                else:
                    with ui.column().classes('empty-state'):
                        ui.label('暂无预警').style(f'font-size: 15px; color: {GRAY_400}; font-weight: 500;')

        def show_alert_detail(alert):
            with ui.dialog() as dialog, ui.card().classes('p-6').style('max-width: 500px;'):
                level = alert['alert_level'] or 'low'
                level_colors = {'high': DANGER, 'medium': WARNING, 'low': PRIMARY}
                ui.label('预警详情').style(f'font-size: 18px; font-weight: 700; color: {GRAY_800}; margin-bottom: 16px;')
                ui.label(f'等级: {level}').style(f'color: {level_colors.get(level, GRAY_500)}; font-weight: 600;')
                ui.label(f'内容: {alert.get("alert_content", "-")}').style(f'font-size: 14px; color: {GRAY_700};')
                ui.separator()
                ui.label('原始消息:').style(f'font-size: 13px; font-weight: 600; color: {GRAY_500};')
                ui.label((alert.get('content') or '-')).style(f'font-size: 13px; color: {GRAY_600}; white-space: pre-wrap;')
                ui.label(f'发送者: {alert.get("sender_name", "-")}').style(f'font-size: 12px; color: {GRAY_400};')
                ui.label(f'时间: {alert["created_at"][:16]}').style(f'font-size: 12px; color: {GRAY_400};')
                if not alert['is_handled']:
                    ui.button('标记为已处理', on_click=lambda: [handle_alert(alert['id']), dialog.close()]).props(f'color={PRIMARY}')
                ui.button('关闭', on_click=dialog.close).props('flat')
            dialog.open()

        # 批量处理按钮
        with ui.row().classes('w-full justify-end mt-2'):
            pending_alerts = db.get_alerts(is_handled=0)
            if pending_alerts:
                ui.button(f'一键处理全部 ({len(pending_alerts)})', on_click=lambda: batch_handle()).props('unelevated').style(f'background: {SUCCESS} !important; color: white !important;')
        
        def batch_handle():
            for a in db.get_alerts(is_handled=0):
                db.handle_alert(a['id'], '管理员')
            ui.notify(f'已处理所有预警', type='positive')
            refresh_alerts()

        refresh_alerts()


def show_stats_tab():
    stats = db.get_stats(days=30)
    cat_colors = {'urgent': DANGER, 'complaint': WARNING, 'repair': '#8B5CF6', 'consult': '#06B6D4', 'chat': '#6B7280', 'other': GRAY_400, 'test': '#EC4899'}

    with ui.card().classes('content-card p-6'):
        with ui.row().classes('w-full items-center justify-between mb-6'):
            ui.label('统计分析').style(f'font-size: 16px; font-weight: 600; color: {GRAY_800};')
            time_range = ui.select(['最近7天', '最近30天'], value='最近30天', label='时间范围').classes('w-32')

        charts_container = ui.column().classes('w-full')

        def render_charts():
            days = 7 if time_range.value == '最近7天' else 30
            stats = db.get_stats(days=days)
            charts_container.clear()

            with charts_container:
                if not stats['category_stats'] and not stats['daily_stats']:
                    with ui.column().classes('empty-state'):
                        ui.label('暂无统计数据').style(f'font-size: 15px; color: {GRAY_400};')
                    return

                with ui.row().classes('w-full gap-6 mb-6'):
                    # 饼图
                    with ui.card().classes('flex-1 p-4').style('border: 1px solid ' + GRAY_200 + '; border-radius: 12px;'):
                        ui.label('消息分类占比').style(f'font-size: 14px; font-weight: 600; color: {GRAY_700}; margin-bottom: 8px;')
                        if stats['category_stats']:
                            pie_data = []
                            for k, v in stats['category_stats'].items():
                                pie_data.append({'name': config.CATEGORIES.get(k, k), 'value': v, 'itemStyle': {'color': cat_colors.get(k, PRIMARY)}})
                            ui.echart({
                                'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)'},
                                'series': [{'type': 'pie', 'radius': '70%', 'data': pie_data, 'label': {'fontSize': 11}}]
                            }).classes('w-full').style('height: 280px')
                        else:
                            ui.label('暂无数据').style(f'font-size: 13px; color: {GRAY_400}; padding: 40px; text-align: center;')

                    # 柱状图
                    with ui.card().classes('flex-1 p-4').style('border: 1px solid ' + GRAY_200 + '; border-radius: 12px;'):
                        ui.label('预警等级分布').style(f'font-size: 14px; font-weight: 600; color: {GRAY_700}; margin-bottom: 8px;')
                        ui.echart({
                            'tooltip': {'trigger': 'axis'},
                            'xAxis': {'type': 'category', 'data': ['紧急', '警告', '提示']},
                            'yAxis': {'type': 'value'},
                            'series': [{'type': 'bar', 'data': [
                                {'value': stats['category_stats'].get('urgent', 0), 'itemStyle': {'color': DANGER}},
                                {'value': stats['category_stats'].get('complaint', 0), 'itemStyle': {'color': WARNING}},
                                {'value': stats['category_stats'].get('repair', 0) + stats['category_stats'].get('consult', 0), 'itemStyle': {'color': PRIMARY}}
                            ], 'barWidth': '50%'}]
                        }).classes('w-full').style('height: 280px')

                # 趋势折线图
                with ui.card().classes('w-full p-4').style('border: 1px solid ' + GRAY_200 + '; border-radius: 12px;'):
                    ui.label('每日消息趋势').style(f'font-size: 14px; font-weight: 600; color: {GRAY_700}; margin-bottom: 8px;')
                    if stats['daily_stats']:
                        dates = [d['date'][-5:] for d in stats['daily_stats']]
                        counts = [d['count'] for d in stats['daily_stats']]
                        ui.echart({
                            'tooltip': {'trigger': 'axis'},
                            'xAxis': {'type': 'category', 'data': dates, 'axisLabel': {'fontSize': 10, 'rotate': 30}},
                            'yAxis': {'type': 'value', 'minInterval': 1},
                            'series': [{'type': 'line', 'data': counts, 'smooth': True, 'areaStyle': {'color': 'rgba(79,70,229,0.1)'}, 'lineStyle': {'color': PRIMARY}, 'itemStyle': {'color': PRIMARY}}]
                        }).classes('w-full').style('height: 250px')
                    else:
                        ui.label('暂无数据').style(f'font-size: 13px; color: {GRAY_400}; padding: 40px; text-align: center;')

        time_range.on('change', lambda _: render_charts())
        render_charts()

        # CSV 导出
        async def export_csv():
            import csv, io
            d = 7 if time_range.value == '最近7天' else 30
            s = db.get_stats(days=d)
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(['分类', '数量'])
            for k, v in s['category_stats'].items():
                w.writerow([config.CATEGORIES.get(k, k), v])
            ui.download(buf.getvalue().encode('utf-8-sig'), f'stats_{d}d.csv', 'text/csv')
        
        ui.button('导出 CSV', on_click=export_csv, icon='download').props(f'color={SUCCESS}').classes('mt-4')


def show_feishu_tab():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    from dotenv import load_dotenv
    load_dotenv(env_path, override=True)
    for attr in ['FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'FEISHU_VERIFICATION_TOKEN', 'FEISHU_ENCRYPT_KEY', 'BOT_MODE']:
        setattr(config, attr, os.getenv(attr, ''))

    feishu_configured = bool(config.FEISHU_APP_ID and config.FEISHU_APP_SECRET and 'your-' not in config.FEISHU_APP_ID)

    # 配置信息卡
    with ui.card().classes('w-full p-6'):
        ui.label('飞书机器人接入').style('font-size: 18px; font-weight: 700; margin-bottom: 16px;')

        if feishu_configured:
            with ui.row().classes('items-center gap-3 mb-4'):
                ui.label('已配置').style(f'font-size: 13px; font-weight: 600; color: {SUCCESS}; background: {SUCCESS_LIGHT}; padding: 4px 12px; border-radius: 12px;')
                ui.label(f'模式: {config.BOT_MODE.upper()}').style(f'font-size: 13px; color: {GRAY_600};')
            
            with ui.card().classes('w-full').style(f'padding: 16px; background: {GRAY_50}; border-radius: 8px;'):
                with ui.row().classes('gap-6'):
                    ui.label(f'App ID: {config.FEISHU_APP_ID}').style(f'font-size: 13px; color: {GRAY_600}; font-family: monospace;')
            
            # 配置编辑表单
            with ui.expansion('修改配置', icon='edit').classes('w-full mt-4'):
                with ui.column().classes('gap-3'):
                    app_id_input = ui.input('App ID', value=config.FEISHU_APP_ID).classes('w-full')
                    app_secret_input = ui.input('App Secret', value=config.FEISHU_APP_SECRET, password=True).classes('w-full')
                    verify_token_input = ui.input('Verification Token', value=config.FEISHU_VERIFICATION_TOKEN or '').classes('w-full')
                    encrypt_key_input = ui.input('Encrypt Key', value=config.FEISHU_ENCRYPT_KEY or '', password=True).classes('w-full')
                    bot_mode_select = ui.select(['sdk', 'webhook'], value=config.BOT_MODE, label='运行模式').classes('w-48')
                    
                    async def save_feishu_config():
                        save_config({
                            'FEISHU_APP_ID': app_id_input.value,
                            'FEISHU_APP_SECRET': app_secret_input.value,
                            'FEISHU_VERIFICATION_TOKEN': verify_token_input.value,
                            'FEISHU_ENCRYPT_KEY': encrypt_key_input.value,
                            'BOT_MODE': bot_mode_select.value
                        })
                        ui.notify('飞书配置已保存', type='positive')
                    
                    ui.button('保存配置', on_click=save_feishu_config, icon='save').props(f'color={PRIMARY}')
        else:
            ui.label('未配置').classes('text-negative')
            ui.label('请在 .env 文件中配置飞书凭证，或使用上方展开面板填写').style(f'font-size: 13px; color: {GRAY_500}; margin-top: 8px;')

    # 机器人控制 + 连接日志
    with ui.card().classes('w-full p-6 mt-4'):
        ui.label('机器人控制').style('font-size: 18px; font-weight: 700; margin-bottom: 16px;')

        with ui.row().classes('items-center gap-4 mb-4'):
            status_indicator = ui.label('')
            log_container = ui.column().classes('w-full')
            
            def update_status():
                status_indicator.clear()
                if app_state['bot_running']:
                    with status_indicator:
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('circle').style(f'color: {SUCCESS}; font-size: 10px;')
                            ui.label('机器人运行中').style(f'font-size: 14px; font-weight: 500; color: {SUCCESS};')
                else:
                    with status_indicator:
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('circle').style(f'color: {GRAY_400}; font-size: 10px;')
                            ui.label('机器人未启动').style(f'font-size: 14px; font-weight: 500; color: {GRAY_500};')
            update_status()

        with ui.row().classes('gap-3'):
            async def start_bot():
                if not feishu_configured:
                    ui.notify('请先完成飞书配置', type='negative')
                    return
                try:
                    bot_dir = os.path.dirname(__file__)
                    script = 'feishu_bot_sdk.py' if config.BOT_MODE == 'sdk' else 'feishu_bot.py'
                    proc = subprocess.Popen([sys.executable, script], cwd=bot_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    app_state['bot_process'] = proc
                    app_state['bot_running'] = True
                    update_status()
                    ui.notify('机器人已启动', type='positive')
                except Exception as e:
                    ui.notify(f'启动失败: {e}', type='negative')

            async def stop_bot():
                if app_state['bot_process']:
                    try:
                        app_state['bot_process'].terminate()
                    except:
                        pass
                    app_state['bot_process'] = None
                    app_state['bot_running'] = False
                    update_status()
                    ui.notify('机器人已停止', type='info')
                else:
                    ui.notify('机器人未在运行', type='warning')

            ui.button('启动机器人', on_click=start_bot, icon='play_arrow').props('unelevated').style(f'background: {PRIMARY} !important; color: white !important;')
            ui.button('停止机器人', on_click=stop_bot, icon='stop').props('unelevated').style(f'background: {GRAY_600} !important; color: white !important;')

        # 连接日志窗口
        with ui.expansion('连接状态日志', icon='terminal').classes('w-full mt-4'):
            log_text = ui.log(max_lines=50).classes('w-full').style(f'height: 200px; font-family: monospace; font-size: 12px; background: {GRAY_900}; color: #E5E7EB; padding: 12px; border-radius: 8px;')
            log_text.push('等待机器人启动...\n')
            
            async def refresh_log():
                if app_state['bot_process']:
                    log_text.push(f'[进程 PID: {app_state["bot_process"].pid}]\n')
                log_text.push(f'[更新时间: {__import__("datetime").datetime.now().strftime("%H:%M:%S")}]\n飞书 App ID: {config.FEISHU_APP_ID}\n运行模式: {config.BOT_MODE}\n')
            
            refresh_log()
            ui.button('刷新日志', on_click=refresh_log, icon='refresh').props('flat').style(f'color: {GRAY_500};')

        # 验证连接
        async def verify_config():
            try:
                import lark_oapi as lark
                client = lark.Client.builder().app_id(config.FEISHU_APP_ID).app_secret(config.FEISHU_APP_SECRET).build()
                resp = client.auth.v3.tenant_access_token.create()
                if resp.success():
                    log_text.push('[验证通过] 飞书凭证有效\n')
                    ui.notify('飞书连接验证通过', type='positive')
                else:
                    log_text.push(f'[验证失败] {resp.msg}\n')
                    ui.notify(f'验证失败: {resp.msg}', type='negative')
            except Exception as e:
                log_text.push(f'[验证错误] {e}\n')
                ui.notify(f'验证错误: {e}', type='negative')
        
        ui.button('验证连接', on_click=verify_config, icon='verified').props('unelevated').style(f'background: {SUCCESS} !important; color: white !important;')


def show_test_tab():
    with ui.card().classes('content-card p-6'):
        ui.label('功能测试').style(f'font-size: 16px; font-weight: 600; color: {GRAY_800}; margin-bottom: 4px;')
        ui.label('输入一条消息，测试 AI 分析效果').style(f'font-size: 14px; color: {GRAY_500}; margin-bottom: 24px;')

        test_input = ui.textarea(
            label='测试消息',
            placeholder='例如：我们楼的电梯又坏了，老人上下楼怎么办啊',
            value='隔壁装修噪音太大了，周末都不休息'
        ).classes('w-full')

        result_card = ui.card().classes('w-full mt-4 hidden').style(f'padding: 24px; background: {GRAY_50}; border-radius: 12px; border: 1px solid {GRAY_200};')

        async def test_analyze():
            if not test_input.value:
                ui.notify('请输入测试消息', type='warning')
                return

            ui.notify('正在分析...', type='info')
            result = analyze_message(test_input.value)

            category = config.CATEGORIES.get(result.get('category'), result.get('category'))
            need_alert = result.get('need_alert', False)
            level = result.get('alert_level', '-')

            level_colors = {'high': DANGER, 'medium': WARNING, 'low': PRIMARY}
            level_labels = {'high': '紧急', 'medium': '警告', 'low': '提示'}

            result_card.classes(remove='hidden')
            result_card.clear()

            with result_card:
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.label('分析结果').style(f'font-size: 15px; font-weight: 600; color: {GRAY_800};')
                    ui.label(category).style(f'font-size: 12px; font-weight: 500; color: white; background: {PRIMARY}; padding: 2px 10px; border-radius: 12px;')
                    if need_alert:
                        level_color = level_colors.get(level, GRAY_500)
                        level_text = level_labels.get(level, '预警')
                        ui.label(level_text).style(f'font-size: 12px; font-weight: 500; color: white; background: {level_color}; padding: 2px 10px; border-radius: 12px;')

                with ui.row().classes('gap-8'):
                    with ui.column().classes('flex-1'):
                        ui.label('摘要').style(f'font-size: 12px; color: {GRAY_500}; margin-bottom: 4px;')
                        ui.label(result.get('summary', '-')).style(f'font-size: 14px; color: {GRAY_800};')

                    with ui.column().classes('flex-1'):
                        ui.label('建议处理').style(f'font-size: 12px; color: {GRAY_500}; margin-bottom: 4px;')
                        ui.label(result.get('suggested_action', '-')).style(f'font-size: 14px; color: {GRAY_800};')

        ui.button('开始分析', icon='psychology', on_click=test_analyze).classes('mt-4').props(f'color={PRIMARY}').classes('btn-primary')

        # 测试历史
        with ui.expansion('测试历史记录', icon='history').classes('w-full mt-6'):
            history_container = ui.column().classes('w-full')
            test_history = []
            
            original_test = test_analyze
            
            async def test_analyze_with_history():
                await original_test()
                if test_input.value:
                    import datetime
                    result = analyze_message(test_input.value)
                    test_history.insert(0, {'msg': test_input.value[:80], 'cat': config.CATEGORIES.get(result.get('category'), result.get('category')), 'sum': result.get('summary', '-'), 'time': datetime.datetime.now().strftime('%H:%M:%S')})
                    if len(test_history) > 20:
                        test_history.pop()
                    refresh_history()
            
            def refresh_history():
                history_container.clear()
                with history_container:
                    if test_history:
                        for item in test_history:
                            with ui.card().classes('w-full p-2 mb-1').style(f'background: {GRAY_50}; border-radius: 6px;'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label(item['time']).style(f'font-size: 11px; color: {GRAY_400};')
                                    ui.label(item['cat']).style(f'font-size: 11px; color: {PRIMARY}; background: {PRIMARY_LIGHT}; padding: 1px 6px; border-radius: 4px;')
                                ui.label(item['msg']).style(f'font-size: 12px; color: {GRAY_700};')
                                ui.label(item['sum']).style(f'font-size: 11px; color: {GRAY_500};')
                    else:
                        ui.label('暂无测试记录').style(f'font-size: 12px; color: {GRAY_400};')
            
            # 替换测试函数
            test_analyze = test_analyze_with_history


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='群小二 - 管理后台',
        port=8501,
        dark=False
    )
