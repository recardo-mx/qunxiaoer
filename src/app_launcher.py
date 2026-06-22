"""群小二 - 桌面应用启动器"""
import sys
import os

# Windows 控制台默认 GBK 不支持 emoji，强制 UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 获取应用根目录
if getattr(sys, 'frozen', False):
    # 打包后：exe 所在目录
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 添加src到路径（开发时需要；打包后 PyInstaller 自动处理）
    sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

# 数据库放在 exe 旁（可写），打包后自动创建 data/ 目录
data_dir = os.path.join(BASE_DIR, 'data')
os.makedirs(data_dir, exist_ok=True)
os.environ['DB_PATH'] = os.path.join(data_dir, 'qunxiaoer.db')


def main():
    """主函数 - 启动原生桌面GUI"""
    from desktop_gui import main as run_gui
    run_gui()


if __name__ == '__main__':
    main()
