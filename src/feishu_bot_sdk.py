"""飞书机器人模块 - SDK长连接模式"""
import json
import sys
import traceback
from typing import Optional

# Windows 控制台默认 GBK 不支持 emoji，强制 UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
try:
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import *
except ImportError:
    print("错误：请先安装 lark-oapi 依赖")
    print("运行: pip install lark-oapi")
    lark = None

from config import config
from llm_service import llm_service
from database import db


class FeishuBotSDK:
    """飞书机器人 - SDK长连接模式"""

    def __init__(self):
        self.ws_client = None
        self.api_client = None

    def _extract_content(self, msg) -> str:
        """提取消息内容"""
        msg_type = msg.message_type
        content_str = msg.content or "{}"

        try:
            content = json.loads(content_str)
        except:
            return content_str

        if msg_type == "text":
            return content.get("text", "")
        elif msg_type == "post":
            title = content.get("title", "")
            texts = []
            for line in content.get("content", []):
                for item in line:
                    if item.get("tag") == "text":
                        texts.append(item.get("text", ""))
            return f"{title} {''.join(texts)}".strip()
        else:
            return f"[{msg_type}消息]"

    def process_message(self, message_data: dict, is_mention: bool = False) -> dict:
        """处理消息：所有消息分类入库，仅 @ 机器人的消息生成回复"""
        content = message_data.get("content", "")
        feishu_msg_id = message_data.get("message_id", "")

        if not content or content.strip() == "":
            return {"action": "skip"}

        # 去重：检查是否已处理过该消息
        if db.message_exists(feishu_msg_id):
            print(f"   ⏭ 消息已处理，跳过: {feishu_msg_id}")
            return {"action": "skip"}

        # 所有消息都进行 LLM 分类并存入数据库
        try:
            analysis = llm_service.analyze_message(content)
        except Exception as e:
            print(f"LLM分析失败: {e}")
            analysis = {
                "category": "other",
                "summary": content[:50],
                "need_alert": False,
                "alert_level": "low",
                "suggested_action": ""
            }

        db_data = {**message_data, **analysis}
        db_id = db.add_message(db_data)

        if analysis.get("need_alert"):
            db.add_alert(
                message_id=db_id,
                alert_level=analysis["alert_level"],
                alert_content=f"[{analysis['category']}] {analysis['summary']}"
            )

        # 更新冲突聚合（行为预测引擎）
        location = analysis.get("location")
        topic = analysis.get("topic")
        if location and topic and analysis.get("category") in ('urgent', 'complaint', 'repair'):
            db.update_issue_cluster(location, topic, analysis.get("alert_level", "low"))

        # 仅 @ 机器人的消息才生成回复
        if is_mention:
            try:
                reply = llm_service.generate_reply(analysis["category"], content)
            except Exception as e:
                print(f"生成回复失败: {e}")
                reply = "收到，已记录您的诉求。"
            return {
                "action": "reply",
                "reply": reply,
                "analysis": analysis,
                "message_id": db_id
            }
        else:
            print(f"   已分类入库: [{analysis['category']}] {analysis['summary'][:40]}")
            return {"action": "save_only"}

    def send_reply(self, chat_id: str, reply: str):
        """发送回复消息"""
        try:
            req = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(CreateMessageRequestBody.builder()
                    .receive_id(chat_id)
                    .msg_type("text")
                    .content(json.dumps({"text": reply}))
                    .build()) \
                .build()

            resp = self.api_client.im.v1.message.create(req)
            if not resp.success():
                print(f"发送回复失败: code={resp.code}, msg={resp.msg}")
            else:
                print(f"回复发送成功: {reply[:30]}...")
        except Exception as e:
            print(f"发送回复错误: {e}")
            traceback.print_exc()

    def _on_message(self, data):
        """处理收到的消息事件（SDK回调）"""
        try:
            event = data.event
            message = event.message
            sender = event.sender

            sender_id = sender.sender_id.open_id if sender and sender.sender_id else "unknown"
            chat_id = message.chat_id
            content = self._extract_content(message)

            # 检测是否 @ 了机器人
            is_mention = False
            if hasattr(message, 'mentions') and message.mentions:
                for m in message.mentions:
                    if hasattr(m, 'mentioned_type') and m.mentioned_type == 'bot':
                        is_mention = True
                        break
            # 兜底：检查消息内容中的 @ 标记
            if not is_mention and "@_user_" in content:
                is_mention = True

            tag = "[@机器人]" if is_mention else "[群消息]"
            print(f"\n📩 收到消息 {tag} | chat_id={chat_id} | sender={sender_id}")
            print(f"   内容: {content[:100]}")

            message_data = {
                "message_id": message.message_id,
                "chat_id": chat_id,
                "sender_id": sender_id,
                "sender_name": "用户",
                "content": content,
                "msg_type": message.message_type,
                "timestamp": message.create_time
            }

            result = self.process_message(message_data, is_mention=is_mention)
            if result.get("action") == "reply":
                self.send_reply(chat_id, result["reply"])
        except Exception as e:
            print(f"处理消息错误: {e}")
            traceback.print_exc()

    def start(self):
        """启动SDK长连接（使用 lark.ws.Client + EventDispatcherHandler）"""
        if not config.FEISHU_APP_ID or not config.FEISHU_APP_SECRET:
            print("错误：未配置飞书凭证")
            return False

        print(f"App ID: {config.FEISHU_APP_ID}")
        print(f"App Secret: {config.FEISHU_APP_SECRET[:8]}***")

        # 创建API客户端（用于发送消息）
        self.api_client = lark.Client.builder() \
            .app_id(config.FEISHU_APP_ID) \
            .app_secret(config.FEISHU_APP_SECRET) \
            .build()
        print("✅ API客户端已创建")

        # 创建事件处理器（使用正确的 EventDispatcherHandler API）
        event_handler = lark.EventDispatcherHandler.builder(
            config.FEISHU_VERIFICATION_TOKEN or "",
            config.FEISHU_ENCRYPT_KEY or ""
        ).register_p2_im_message_receive_v1(
            self._on_message
        ).build()
        print("✅ 事件处理器已注册: im.message.receive_v1")

        # 创建长连接客户端（使用正确的 lark.ws.Client API）
        self.ws_client = lark.ws.Client(
            app_id=config.FEISHU_APP_ID,
            app_secret=config.FEISHU_APP_SECRET,
            event_handler=event_handler,
            log_level=lark.LogLevel.DEBUG
        )

        print("🚀 飞书SDK长连接模式启动中...")
        print("   (按 Ctrl+C 停止)")
        self.ws_client.start()
        return True

    def stop(self):
        """停止长连接"""
        if self.ws_client:
            print("飞书SDK长连接已停止")
            self.ws_client.stop()


bot_sdk = FeishuBotSDK()


if __name__ == "__main__":
    print("=== 飞书机器人 (SDK长连接模式) ===")
    print("按 Ctrl+C 停止")
    try:
        bot_sdk.start()
    except KeyboardInterrupt:
        print("\n机器人已停止")
