"""测试消息分析功能"""
import sys
import os
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)

from llm_service import llm_service
from database import db


def test_message_analysis():
    """测试消息分析"""
    test_messages = [
        {"content": "我们楼的电梯又坏了，老人上下楼怎么办啊", "expected": "urgent"},
        {"content": "今天天气真好，大家早上好", "expected": "chat"},
        {"content": "隔壁装修噪音太大了，周末都不休息", "expected": "complaint"},
        {"content": "小区门口的路灯坏了好几天了", "expected": "repair"},
        {"content": "请问物业费怎么交？", "expected": "consult"},
        {"content": "6栋2单元漏水了，水都流到楼道了", "expected": "urgent"},
    ]

    print("=" * 60)
    print("群小二 - 消息分析测试")
    print("=" * 60)

    # 测试连接
    print("\n[1] 测试LLM连接...")
    if llm_service.test_connection():
        print("✓ LLM连接成功")
    else:
        print("✗ LLM连接失败，请检查配置")
        return

    # 测试分析
    print("\n[2] 测试消息分析...")
    correct = 0
    total = len(test_messages)

    for i, msg in enumerate(test_messages, 1):
        content = msg["content"]
        expected = msg["expected"]

        result = llm_service.analyze_message(content)
        actual = result.get("category", "other")
        match = "✓" if actual == expected else "✗"

        if actual == expected:
            correct += 1

        print(f"\n测试 {i}: {match}")
        print(f"  消息: {content}")
        print(f"  期望: {expected}")
        print(f"  实际: {actual}")
        print(f"  摘要: {result.get('summary', '-')}")
        print(f"  预警: {result.get('need_alert', False)}")

    print("\n" + "=" * 60)
    print(f"测试结果: {correct}/{total} 通过 ({correct/total*100:.1f}%)")
    print("=" * 60)


def test_database():
    """测试数据库"""
    print("\n[3] 测试数据库...")

    # 添加测试消息
    test_data = {
        "message_id": "test_001",
        "chat_id": "chat_001",
        "sender_id": "user_001",
        "sender_name": "测试用户",
        "content": "测试消息内容",
        "category": "test",
        "summary": "测试摘要",
        "need_alert": False,
        "alert_level": "low",
        "suggested_action": "测试处理"
    }

    msg_id = db.add_message(test_data)
    print(f"✓ 添加消息成功，ID: {msg_id}")

    # 查询消息
    messages = db.get_messages(limit=10)
    print(f"✓ 查询消息成功，共 {len(messages)} 条")

    # 获取统计
    stats = db.get_stats(days=1)
    print(f"✓ 获取统计成功")


if __name__ == "__main__":
    test_message_analysis()
    test_database()
