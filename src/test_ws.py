"""飞书机器人 - SDK长连接测试"""
import json
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from config import config

print(f"App ID: {config.FEISHU_APP_ID}")
print(f"App Secret: {config.FEISHU_APP_SECRET[:10]}...")

# 消息处理函数
def handle_message(data):
    print(f"\n{'='*50}")
    print(f"收到消息事件!")
    print(f"事件数据: {data}")
    try:
        message = data.event.message
        chat_id = message.chat_id
        content = json.loads(message.content).get("text", "")
        print(f"聊天ID: {chat_id}")
        print(f"消息内容: {content}")

        # 发送回复
        client = lark.Client.builder() \
            .app_id(config.FEISHU_APP_ID) \
            .app_secret(config.FEISHU_APP_SECRET) \
            .build()

        req = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content(json.dumps({"text": f"收到: {content}"}))
                .build()) \
            .build()

        resp = client.im.v1.message.create(req)
        if resp.success():
            print("回复成功!")
        else:
            print(f"回复失败: {resp.msg}")
    except Exception as e:
        print(f"处理错误: {e}")
        import traceback
        traceback.print_exc()
    print(f"{'='*50}\n")

# 创建事件处理器
event_handler = lark.EventDispatcherHandler.builder(
    "", ""
).register_p2_im_message_receive_v1(
    handle_message
).build()

# 创建长连接客户端
ws_client = lark.ws.Client(
    app_id=config.FEISHU_APP_ID,
    app_secret=config.FEISHU_APP_SECRET,
    event_handler=event_handler,
    log_level=lark.LogLevel.DEBUG
)

print("启动SDK长连接...")
ws_client.start()
