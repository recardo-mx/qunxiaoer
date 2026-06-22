"""配置管理模块"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Config:
    """应用配置"""

    # LLM配置
    LLM_MODE = os.getenv("LLM_MODE", "api")  # "ollama" 或 "api"

    # Ollama配置
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:7b")

    # API配置（通义千问/DeepSeek）
    API_KEY = os.getenv("API_KEY", "")
    API_BASE_URL = os.getenv("API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    API_MODEL = os.getenv("API_MODEL", "qwen-plus")

    # 飞书配置
    BOT_MODE = os.getenv("BOT_MODE", "webhook")  # "webhook" 或 "sdk"
    FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
    FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
    FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
    FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")

    # 服务配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    WEB_PORT = int(os.getenv("WEB_PORT", "8501"))

    # 数据库
    DB_PATH = os.getenv("DB_PATH", "data/qunxiaoer.db")

    # 预警配置
    ALERT_KEYWORDS = ["电梯故障", "漏水", "火灾", "受伤", "紧急", "急救", "打架", "盗窃"]

    # 消息分类
    CATEGORIES = {
        "urgent": "紧急诉求",
        "complaint": "投诉建议",
        "repair": "报修维修",
        "consult": "咨询求助",
        "chat": "日常闲聊",
        "other": "其他"
    }


config = Config()
