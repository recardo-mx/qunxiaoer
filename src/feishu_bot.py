"""飞书机器人模块"""
import json
import hashlib
from typing import Optional
from flask import Flask, request, jsonify
from config import config
from llm_service import llm_service
from database import db


app = Flask(__name__)


class FeishuBot:
    """飞书机器人"""

    def __init__(self):
        self.message_handlers = []

    def verify_signature(self, timestamp: str, nonce: str, body: str) -> str:
        """验证签名"""
        sign_str = timestamp + nonce + config.FEISHU_ENCRYPT_KEY + body
        return hashlib.sha256(sign_str.encode()).hexdigest()

    def parse_message(self, event: dict) -> Optional[dict]:
        """解析飞书消息事件"""
        try:
            msg = event.get("message", {})
            sender = event.get("sender", {})

            return {
                "message_id": msg.get("message_id"),
                "chat_id": msg.get("chat_id"),
                "sender_id": sender.get("sender_id", {}).get("open_id"),
                "sender_name": sender.get("sender_id", {}).get("name", "未知用户"),
                "content": self._extract_content(msg),
                "msg_type": msg.get("message_type"),
                "timestamp": msg.get("create_time")
            }
        except Exception as e:
            print(f"解析消息错误: {e}")
            return None

    def _extract_content(self, msg: dict) -> str:
        """提取消息内容"""
        msg_type = msg.get("message_type")
        content_str = msg.get("content", "{}")

        try:
            content = json.loads(content_str)
        except:
            return content_str

        if msg_type == "text":
            return content.get("text", "")
        elif msg_type == "post":
            # 富文本消息
            title = content.get("title", "")
            texts = []
            for line in content.get("content", []):
                for item in line:
                    if item.get("tag") == "text":
                        texts.append(item.get("text", ""))
            return f"{title} {''.join(texts)}".strip()
        else:
            return f"[{msg_type}消息]"

    def process_message(self, message_data: dict) -> dict:
        """处理消息"""
        content = message_data.get("content", "")

        # 跳过空消息
        if not content or content.strip() == "":
            return {"action": "skip"}

        # 跳过@机器人本身的消息
        if "@_user" in content:
            return {"action": "skip"}

        # LLM分析
        analysis = llm_service.analyze_message(content)

        # 保存到数据库
        db_data = {**message_data, **analysis}
        message_id = db.add_message(db_data)

        # 生成回复
        reply = llm_service.generate_reply(analysis["category"], content)

        # 处理预警
        if analysis["need_alert"]:
            db.add_alert(
                message_id=message_id,
                alert_level=analysis["alert_level"],
                alert_content=f"[{analysis['category']}] {analysis['summary']}"
            )

        return {
            "action": "reply",
            "reply": reply,
            "analysis": analysis,
            "message_id": message_id
        }


# 全局实例
bot = FeishuBot()


@app.route("/webhook/event", methods=["POST"])
def handle_event():
    """处理飞书事件回调"""
    data = request.json

    # URL验证
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    # 签名验证
    if config.FEISHU_ENCRYPT_KEY:
        timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
        nonce = request.headers.get("X-Lark-Request-Nonce", "")
        body = request.get_data(as_text=True)
        expected_sign = bot.verify_signature(timestamp, nonce, body)
        actual_sign = request.headers.get("X-Lark-Signature", "")
        if expected_sign != actual_sign:
            return jsonify({"error": "签名验证失败"}), 403

    # 处理事件
    header = data.get("header", {})
    event_type = header.get("event_type")

    if event_type == "im.message.receive_v1":
        event = data.get("event", {})
        message_data = bot.parse_message(event)

        if message_data:
            result = bot.process_message(message_data)
            return jsonify(result)

    return jsonify({"code": 0})


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "mode": config.LLM_MODE})


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT)
