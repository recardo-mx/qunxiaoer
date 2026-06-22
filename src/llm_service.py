"""LLM服务模块 - 支持Ollama和API两种模式"""
import json
from typing import Optional
from openai import OpenAI
from config import config


class LLMService:
    """统一的LLM服务接口"""

    def __init__(self):
        self._init_client()

    def _init_client(self):
        """初始化LLM客户端"""
        if config.LLM_MODE == "ollama":
            self.client = OpenAI(
                base_url=config.OLLAMA_BASE_URL + "/v1",
                api_key="ollama"
            )
            self.model = config.OLLAMA_MODEL
        else:
            self.client = OpenAI(
                base_url=config.API_BASE_URL,
                api_key=config.API_KEY
            )
            self.model = config.API_MODEL

    def analyze_message(self, message: str) -> dict:
        """分析消息，返回分类和摘要"""
        prompt = f"""你是一个社区网格员助手，负责分析微信群里的居民消息。

请分析以下消息，返回JSON格式结果：
{{
    "category": "分类（urgent/complaint/repair/consult/chat/other）",
    "summary": "一句话摘要",
    "location": "消息涉及的具体地点（如6栋、3单元、小区门口、游泳池等），没有则填null",
    "topic": "消息涉及的核心问题类型（如电梯故障、漏水、噪音、报修、咨询等），没有则填null",
    "need_alert": true/false,
    "alert_level": "high/medium/low",
    "suggested_action": "建议处理方式"
}}

分类说明：
- urgent: 紧急事件（火灾、漏水、电梯故障、受伤等）
- complaint: 投诉建议（噪音、环境、服务等）
- repair: 报修维修（设施损坏、设备故障等）
- consult: 咨询求助（问政策、问流程等）
- chat: 日常闲聊、问候
- other: 其他

居民消息：{message}

请直接返回JSON，不要添加其他文字。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            content = response.choices[0].message.content
            # 提取JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except Exception as e:
            print(f"LLM分析错误: {e}")
            return {
                "category": "other",
                "summary": message[:50],
                "location": None,
                "topic": None,
                "need_alert": False,
                "alert_level": "low",
                "suggested_action": "人工复核"
            }

    def generate_reply(self, category: str, message: str) -> str:
        """根据分类生成回复"""
        system_prompt = """你是「群小二」，一名专业的社区网格员助手，在居民微信群里工作。

你的职责：
1. 处理居民的各种诉求——紧急事件、投诉建议、报修维修、咨询求助
2. 安抚居民情绪，告知处理进度
3. 引导居民通过正规渠道解决问题

你的风格：
- 正式但不生硬，有温度但不闲聊
- 每次回复都要体现"已记录、在处理、有反馈"
- 紧急事件要强调安全第一
- 不要扮演闲聊机器人，不要用卖萌、颜文字、表情包
- 只回复与社区治理相关的内容"""

        category_guides = {
            "urgent": "居民报告了紧急事件。请：1)安抚情绪 2)强调安全注意事项 3)告知已通知相关人员 4)给出预计处理时间。语气要沉稳、让人安心。",
            "complaint": "居民有投诉建议。请：1)感谢反馈 2)表示理解和重视 3)告知已记录并会跟进 4)给出大致处理流程。",
            "repair": "居民需要报修。请：1)确认报修内容 2)告知已登记工单 3)说明处理流程和时间 4)提供联系方式。",
            "consult": "居民有咨询问题。请：1)直接回答或指引 2)如不确定则告知会核实后回复 3)提供相关渠道信息。",
            "chat": "居民在闲聊/打招呼。简短友好回应，表明群小二身份，引导有需求时@你即可。不要展开闲聊。",
            "other": "简短回应，表明已收到消息，引导居民明确诉求。"
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{category_guides.get(category, category_guides['other'])}\n\n居民消息：{message}\n\n请生成群小二的回复："}
                ],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"生成回复错误: {e}")
            return "收到，已记录您的诉求，会尽快处理。"

    def test_connection(self) -> bool:
        """测试LLM连接"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False


# 全局实例
llm_service = LLMService()
