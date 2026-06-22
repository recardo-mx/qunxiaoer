"""群小二 - 原生桌面GUI版本"""
import sys
import os
import json
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta

# Windows 控制台默认 GBK 不支持 emoji，强制 UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 获取应用根目录
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    sys.path.insert(0, os.path.join(BASE_DIR, '_internal'))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, BASE_DIR)

# 数据库放在 exe 旁（可写）
data_dir = os.path.join(BASE_DIR, 'data')
os.makedirs(data_dir, exist_ok=True)
os.environ['DB_PATH'] = os.path.join(data_dir, 'qunxiaoer.db')

# 导入项目模块
from config import config
from database import db


class ScrollableFrame(ttk.Frame):
    """可滚动的Frame"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)


class SetupDialog(tk.Toplevel):
    """首次配置对话框"""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("群小二 - 首次配置向导")
        self.geometry("600x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.llm_mode = tk.StringVar(value="api")

        self._create_widgets()

    def _create_widgets(self):
        # 标题
        title_frame = ttk.Frame(self, padding=20)
        title_frame.pack(fill="x")
        ttk.Label(title_frame, text="群小二 - 首次配置向导", font=("微软雅黑", 16, "bold")).pack()
        ttk.Label(title_frame, text="群众诉求智能分拣与预警系统", foreground="gray").pack(pady=(5, 0))

        # 分隔线
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # 步骤1：选择LLM模式
        step1_frame = ttk.LabelFrame(self, text="步骤 1: 选择AI模型", padding=15)
        step1_frame.pack(fill="x", padx=20, pady=10)

        ttk.Radiobutton(step1_frame, text="API（云端调用）- 开箱即用，按量付费",
                        variable=self.llm_mode, value="api").pack(anchor="w")
        ttk.Radiobutton(step1_frame, text="Ollama（本地部署）- 完全免费，数据不出内网",
                        variable=self.llm_mode, value="ollama").pack(anchor="w")

        # 步骤2：配置表单
        step2_frame = ttk.LabelFrame(self, text="步骤 2: 配置参数", padding=15)
        step2_frame.pack(fill="x", padx=20, pady=10)

        # API配置
        self.api_frame = ttk.Frame(step2_frame)
        self.api_frame.pack(fill="x")

        ttk.Label(self.api_frame, text="API Key:").grid(row=0, column=0, sticky="w", pady=5)
        self.api_key_entry = ttk.Entry(self.api_frame, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)

        ttk.Label(self.api_frame, text="API地址:").grid(row=1, column=0, sticky="w", pady=5)
        self.api_url_entry = ttk.Entry(self.api_frame, width=50)
        self.api_url_entry.insert(0, "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.api_url_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)

        ttk.Label(self.api_frame, text="模型名称:").grid(row=2, column=0, sticky="w", pady=5)
        self.api_model_entry = ttk.Entry(self.api_frame, width=50)
        self.api_model_entry.insert(0, "qwen-plus")
        self.api_model_entry.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)

        self.api_frame.columnconfigure(1, weight=1)

        # Ollama配置
        self.ollama_frame = ttk.Frame(step2_frame)

        ttk.Label(self.ollama_frame, text="Ollama地址:").grid(row=0, column=0, sticky="w", pady=5)
        self.ollama_url_entry = ttk.Entry(self.ollama_frame, width=50)
        self.ollama_url_entry.insert(0, "http://localhost:11434")
        self.ollama_url_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)

        ttk.Label(self.ollama_frame, text="模型名称:").grid(row=1, column=0, sticky="w", pady=5)
        self.ollama_model_entry = ttk.Entry(self.ollama_frame, width=50)
        self.ollama_model_entry.insert(0, "qwen2:7b")
        self.ollama_model_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)

        self.ollama_frame.columnconfigure(1, weight=1)

        # 切换显示
        self.llm_mode.trace("w", self._on_mode_change)

        # 按钮
        btn_frame = ttk.Frame(self, padding=20)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="保存并测试", command=self._save_and_test).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side="right", padx=5)

    def _on_mode_change(self, *args):
        if self.llm_mode.get() == "api":
            self.ollama_frame.pack_forget()
            self.api_frame.pack(fill="x")
        else:
            self.api_frame.pack_forget()
            self.ollama_frame.pack(fill="x")

    def _save_and_test(self):
        mode = self.llm_mode.get()

        if mode == "api":
            api_key = self.api_key_entry.get().strip()
            if not api_key:
                messagebox.showerror("错误", "请输入API Key")
                return

            updates = {
                'LLM_MODE': 'api',
                'API_KEY': api_key,
                'API_BASE_URL': self.api_url_entry.get().strip(),
                'API_MODEL': self.api_model_entry.get().strip()
            }
        else:
            updates = {
                'LLM_MODE': 'ollama',
                'OLLAMA_BASE_URL': self.ollama_url_entry.get().strip(),
                'OLLAMA_MODEL': self.ollama_model_entry.get().strip()
            }

        self._save_config(updates)

        # 测试连接
        try:
            from llm_service import llm_service
            if llm_service.test_connection():
                messagebox.showinfo("成功", "配置已保存，连接测试成功！")
                self.result = mode
                self.destroy()
            else:
                messagebox.showerror("失败", "连接测试失败，请检查配置")
        except Exception as e:
            messagebox.showerror("错误", f"连接测试失败: {e}")

    def _save_config(self, updates):
        env_path = os.path.join(BASE_DIR, '.env')
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        new_lines = []
        updated_keys = set()

        for line in lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('#'):
                key = line_stripped.split('=')[0]
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")

        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)

    def cancel(self):
        self.result = None
        self.destroy()


class MainApplication(ttk.Frame):
    """主应用程序"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.pack(fill="both", expand=True)

        self._create_menu()
        self._create_main_layout()
        self._show_overview()

    def _create_menu(self):
        menubar = tk.Menu(self.parent)
        self.parent.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="重新配置", command=self._show_setup)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.parent.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="数据概览", command=self._show_overview)
        view_menu.add_command(label="消息记录", command=self._show_messages)
        view_menu.add_command(label="预警管理", command=self._show_alerts)
        view_menu.add_command(label="统计分析", command=self._show_stats)
        view_menu.add_command(label="手动测试", command=self._show_test)
        menubar.add_cascade(label="视图", menu=view_menu)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

    def _create_main_layout(self):
        # 顶部状态栏
        status_frame = ttk.Frame(self, relief="sunken", borderwidth=1)
        status_frame.pack(fill="x", side="bottom")

        self.status_label = ttk.Label(status_frame, text="就绪", padding=5)
        self.status_label.pack(side="left")

        mode_text = f"LLM模式: {config.LLM_MODE}"
        if config.LLM_MODE == "ollama":
            mode_text += f" | {config.OLLAMA_MODEL}"
        else:
            mode_text += f" | {config.API_MODEL}"
        ttk.Label(status_frame, text=mode_text, padding=5).pack(side="right")

        # 左侧导航栏
        nav_frame = ttk.Frame(self, width=150, relief="raised", borderwidth=1)
        nav_frame.pack(fill="y", side="left")
        nav_frame.pack_propagate(False)

        ttk.Label(nav_frame, text="功能菜单", font=("微软雅黑", 10, "bold")).pack(pady=10)

        buttons = [
            ("数据概览", self._show_overview),
            ("消息记录", self._show_messages),
            ("预警管理", self._show_alerts),
            ("统计分析", self._show_stats),
            ("手动测试", self._show_test),
        ]

        for text, command in buttons:
            btn = ttk.Button(nav_frame, text=text, command=command, width=15)
            btn.pack(pady=5, padx=10)

        # 主内容区
        self.content_frame = ttk.Frame(self, relief="sunken", borderwidth=1)
        self.content_frame.pack(fill="both", expand=True, side="right")

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_overview(self):
        self._clear_content()
        self.status_label.config(text="数据概览")

        # 创建可滚动区域
        scroll_frame = ScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True)
        frame = scroll_frame.scrollable_frame

        # 统计卡片
        stats = db.get_stats(days=7)
        total = sum(stats['category_stats'].values())
        urgent = stats['category_stats'].get('urgent', 0)
        alert_total = stats['alert_stats'].get('total', 0)
        alert_handled = stats['alert_stats'].get('handled', 0)

        cards_frame = ttk.Frame(frame)
        cards_frame.pack(fill="x", padx=10, pady=10)

        # 卡片1：消息总数
        card1 = ttk.LabelFrame(cards_frame, text="本周消息总数", padding=15)
        card1.pack(side="left", fill="both", expand=True, padx=5)
        ttk.Label(card1, text=str(total), font=("微软雅黑", 24, "bold"), foreground="blue").pack()

        # 卡片2：紧急诉求
        card2 = ttk.LabelFrame(cards_frame, text="紧急诉求", padding=15)
        card2.pack(side="left", fill="both", expand=True, padx=5)
        ttk.Label(card2, text=str(urgent), font=("微软雅黑", 24, "bold"), foreground="red").pack()

        # 卡片3：预警总数
        card3 = ttk.LabelFrame(cards_frame, text="预警总数", padding=15)
        card3.pack(side="left", fill="both", expand=True, padx=5)
        ttk.Label(card3, text=str(alert_total), font=("微软雅黑", 24, "bold"), foreground="orange").pack()

        # 卡片4：处理率
        card4 = ttk.LabelFrame(cards_frame, text="处理率", padding=15)
        card4.pack(side="left", fill="both", expand=True, padx=5)
        rate = f"{alert_handled/alert_total*100:.1f}%" if alert_total > 0 else "0%"
        ttk.Label(card4, text=rate, font=("微软雅黑", 24, "bold"), foreground="green").pack()

        # 最近预警
        alert_frame = ttk.LabelFrame(frame, text="最近预警", padding=10)
        alert_frame.pack(fill="x", padx=10, pady=10)

        alerts = db.get_alerts(is_handled=0)[:5]
        if alerts:
            for alert in alerts:
                alert_row = ttk.Frame(alert_frame)
                alert_row.pack(fill="x", pady=2)

                ttk.Label(alert_row, text=f"[{alert['alert_level']}]",
                         foreground="red", width=8).pack(side="left")
                ttk.Label(alert_row, text=alert['alert_content'][:50],
                         width=40).pack(side="left", padx=5)
                ttk.Label(alert_row, text=alert['created_at'][:16],
                         foreground="gray").pack(side="left", padx=5)
                ttk.Button(alert_row, text="处理",
                          command=lambda a=alert: self._handle_alert(a['id'])).pack(side="right", padx=5)
        else:
            ttk.Label(alert_frame, text="暂无未处理预警", foreground="gray").pack()

    def _show_messages(self):
        self._clear_content()
        self.status_label.config(text="消息记录")

        scroll_frame = ScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True)
        frame = scroll_frame.scrollable_frame

        # 筛选区
        filter_frame = ttk.LabelFrame(frame, text="筛选条件", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(filter_frame, text="分类:").pack(side="left", padx=5)
        category_var = tk.StringVar(value="全部")
        categories = ["全部"] + list(config.CATEGORIES.values())
        category_combo = ttk.Combobox(filter_frame, textvariable=category_var,
                                      values=categories, state="readonly", width=15)
        category_combo.pack(side="left", padx=5)

        ttk.Label(filter_frame, text="条数:").pack(side="left", padx=5)
        limit_var = tk.StringVar(value="100")
        limit_entry = ttk.Entry(filter_frame, textvariable=limit_var, width=10)
        limit_entry.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="查询",
                  command=lambda: self._refresh_messages(category_var.get(), limit_var.get())).pack(side="left", padx=10)

        # 消息表格
        self.messages_tree = ttk.Treeview(frame, columns=("time", "sender", "content", "category", "summary", "level"),
                                          show="headings", height=20)
        self.messages_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # 设置列标题
        self.messages_tree.heading("time", text="时间")
        self.messages_tree.heading("sender", text="发送者")
        self.messages_tree.heading("content", text="内容")
        self.messages_tree.heading("category", text="分类")
        self.messages_tree.heading("summary", text="摘要")
        self.messages_tree.heading("level", text="预警等级")

        # 设置列宽
        self.messages_tree.column("time", width=120)
        self.messages_tree.column("sender", width=80)
        self.messages_tree.column("content", width=250)
        self.messages_tree.column("category", width=80)
        self.messages_tree.column("summary", width=200)
        self.messages_tree.column("level", width=60)

        # 滚动条
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.messages_tree.yview)
        self.messages_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self._refresh_messages("全部", "100")

    def _refresh_messages(self, category, limit):
        # 清空现有数据
        for item in self.messages_tree.get_children():
            self.messages_tree.delete(item)

        try:
            limit = int(limit)
        except:
            limit = 100

        # 查询数据
        if category == "全部":
            messages = db.get_messages(limit=limit)
        else:
            cat_key = [k for k, v in config.CATEGORIES.items() if v == category][0]
            messages = db.get_messages(limit=limit, category=cat_key)

        for msg in messages:
            self.messages_tree.insert("", "end", values=(
                msg['created_at'][:16] if msg['created_at'] else '-',
                msg['sender_name'] or '-',
                (msg['content'][:50] + '...') if len(msg['content'] or '') > 50 else msg['content'],
                config.CATEGORIES.get(msg['category'], msg['category']),
                msg['summary'] or '-',
                msg['alert_level'] or '-'
            ))

    def _show_alerts(self):
        self._clear_content()
        self.status_label.config(text="预警管理")

        scroll_frame = ScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True)
        frame = scroll_frame.scrollable_frame

        # 待处理预警
        pending_frame = ttk.LabelFrame(frame, text="待处理预警", padding=10)
        pending_frame.pack(fill="x", padx=10, pady=10)

        alerts = db.get_alerts(is_handled=0)
        if alerts:
            for alert in alerts:
                alert_row = ttk.Frame(pending_frame)
                alert_row.pack(fill="x", pady=5)

                ttk.Label(alert_row, text=f"[{alert['alert_level']}]",
                         foreground="red", font=("微软雅黑", 9, "bold")).pack(side="left", anchor="n")

                info_frame = ttk.Frame(alert_row)
                info_frame.pack(side="left", fill="x", expand=True, padx=10)

                ttk.Label(info_frame, text=alert['alert_content'],
                         wraplength=400).pack(anchor="w")
                ttk.Label(info_frame, text=f"消息: {alert['content'][:80]}",
                         foreground="gray").pack(anchor="w")
                ttk.Label(info_frame, text=f"发送者: {alert['sender_name']} | 时间: {alert['created_at'][:16]}",
                         foreground="gray").pack(anchor="w")

                ttk.Button(alert_row, text="标记已处理",
                          command=lambda a=alert: self._handle_alert(a['id'])).pack(side="right", padx=5)
        else:
            ttk.Label(pending_frame, text="暂无待处理预警", foreground="gray").pack()

    def _show_stats(self):
        self._clear_content()
        self.status_label.config(text="统计分析")

        scroll_frame = ScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True)
        frame = scroll_frame.scrollable_frame

        stats = db.get_stats(days=7)

        # 分类统计
        cat_frame = ttk.LabelFrame(frame, text="消息分类分布", padding=10)
        cat_frame.pack(fill="x", padx=10, pady=10)

        if stats['category_stats']:
            max_count = max(stats['category_stats'].values()) if stats['category_stats'] else 1
            for category, count in stats['category_stats'].items():
                label = config.CATEGORIES.get(category, category)
                row = ttk.Frame(cat_frame)
                row.pack(fill="x", pady=2)

                ttk.Label(row, text=label, width=10).pack(side="left")

                # 进度条
                progress = ttk.Progressbar(row, length=300, mode="determinate")
                progress['value'] = (count / max_count) * 100
                progress.pack(side="left", padx=10, fill="x", expand=True)

                ttk.Label(row, text=str(count), width=8).pack(side="right")
        else:
            ttk.Label(cat_frame, text="暂无数据", foreground="gray").pack()

        # 每日趋势
        daily_frame = ttk.LabelFrame(frame, text="每日消息趋势", padding=10)
        daily_frame.pack(fill="x", padx=10, pady=10)

        if stats['daily_stats']:
            for day in stats['daily_stats'][-7:]:  # 最近7天
                row = ttk.Frame(daily_frame)
                row.pack(fill="x", pady=2)

                ttk.Label(row, text=day['date'], width=12).pack(side="left")

                progress = ttk.Progressbar(row, length=300, mode="determinate")
                max_daily = max(d['count'] for d in stats['daily_stats']) if stats['daily_stats'] else 1
                progress['value'] = (day['count'] / max_daily) * 100
                progress.pack(side="left", padx=10, fill="x", expand=True)

                ttk.Label(row, text=str(day['count']), width=8).pack(side="right")
        else:
            ttk.Label(daily_frame, text="暂无数据", foreground="gray").pack()

    def _show_test(self):
        self._clear_content()
        self.status_label.config(text="手动测试")

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="手动测试", font=("微软雅黑", 14, "bold")).pack(anchor="w", pady=(0, 10))

        # 输入区
        input_frame = ttk.LabelFrame(frame, text="输入测试消息", padding=10)
        input_frame.pack(fill="x", pady=10)

        self.test_input = tk.Text(input_frame, height=4, width=60)
        self.test_input.pack(fill="x")
        self.test_input.insert("1.0", "我们楼的电梯又坏了，老人上下楼怎么办啊")

        ttk.Button(input_frame, text="分析消息", command=self._test_analyze).pack(pady=10)

        # 结果区
        result_frame = ttk.LabelFrame(frame, text="分析结果", padding=10)
        result_frame.pack(fill="x", pady=10)

        self.test_result = tk.Text(result_frame, height=8, width=60, state="disabled")
        self.test_result.pack(fill="x")

    def _test_analyze(self):
        message = self.test_input.get("1.0", "end").strip()
        if not message:
            messagebox.showwarning("警告", "请输入测试消息")
            return

        self.status_label.config(text="正在分析...")
        self.update()

        try:
            from llm_service import llm_service
            result = llm_service.analyze_message(message)

            self.test_result.config(state="normal")
            self.test_result.delete("1.0", "end")
            self.test_result.insert("1.0", f"""分类: {config.CATEGORIES.get(result.get('category'), result.get('category'))}
摘要: {result.get('summary')}
需要预警: {'是' if result.get('need_alert') else '否'}
预警等级: {result.get('alert_level', '-')}
建议处理: {result.get('suggested_action', '-')}""")
            self.test_result.config(state="disabled")

            self.status_label.config(text="分析完成")
        except Exception as e:
            messagebox.showerror("错误", f"分析失败: {e}")
            self.status_label.config(text="分析失败")

    def _handle_alert(self, alert_id):
        db.handle_alert(alert_id, '管理员')
        messagebox.showinfo("成功", "已标记为已处理")
        self._show_overview()  # 刷新概览

    def _show_setup(self):
        dialog = SetupDialog(self.parent)
        self.parent.wait_window(dialog)
        if dialog.result:
            self._show_overview()

    def _show_about(self):
        messagebox.showinfo("关于", "群小二 - 群众诉求智能分拣与预警系统\n\n版本: 1.0\n\n企业AI场景实战课程作业")


def check_config():
    """检查配置是否完整"""
    env_path = os.path.join(BASE_DIR, '.env')
    if not os.path.exists(env_path):
        return False
    if config.LLM_MODE == "api" and not config.API_KEY:
        return False
    return True


def main():
    """主函数"""
    root = tk.Tk()
    root.title("群小二 - 群众诉求智能分拣与预警系统")
    root.geometry("1000x700")
    root.minsize(800, 600)

    # 设置图标（如果存在）
    try:
        if sys.platform == "win32":
            root.iconbitmap(default="icon.ico")
    except:
        pass

    # 检查配置
    if not check_config():
        dialog = SetupDialog(root)
        root.wait_window(dialog)
        if not dialog.result:
            root.destroy()
            return

    # 启动主应用
    app = MainApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
