"""数据库模块 - SQLite存储"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from config import config


class Database:
    """SQLite数据库管理"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self._init_db()

    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # 消息记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT,
                chat_id TEXT,
                sender_id TEXT,
                sender_name TEXT,
                content TEXT,
                category TEXT,
                summary TEXT,
                need_alert INTEGER DEFAULT 0,
                alert_level TEXT,
                suggested_action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 预警记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                alert_level TEXT,
                alert_content TEXT,
                is_handled INTEGER DEFAULT 0,
                handled_by TEXT,
                handled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        ''')

        # 统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                total_messages INTEGER DEFAULT 0,
                urgent_count INTEGER DEFAULT 0,
                complaint_count INTEGER DEFAULT 0,
                repair_count INTEGER DEFAULT 0,
                consult_count INTEGER DEFAULT 0,
                chat_count INTEGER DEFAULT 0,
                alert_count INTEGER DEFAULT 0,
                UNIQUE(date)
            )
        ''')

        conn.commit()
        conn.close()

    def message_exists(self, message_id: str) -> bool:
        """检查消息是否已存在（去重）"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM messages WHERE message_id = ?', (message_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def add_message(self, data: dict) -> int:
        """添加消息记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (message_id, chat_id, sender_id, sender_name,
                                  content, category, summary, need_alert, alert_level, suggested_action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('message_id'),
            data.get('chat_id'),
            data.get('sender_id'),
            data.get('sender_name'),
            data.get('content'),
            data.get('category'),
            data.get('summary'),
            1 if data.get('need_alert') else 0,
            data.get('alert_level'),
            data.get('suggested_action')
        ))
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id

    def add_alert(self, message_id: int, alert_level: str, alert_content: str):
        """添加预警记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alerts (message_id, alert_level, alert_content)
            VALUES (?, ?, ?)
        ''', (message_id, alert_level, alert_content))
        conn.commit()
        conn.close()

    def get_messages(self, limit: int = 100, category: str = None) -> List[Dict]:
        """获取消息列表"""
        conn = self._get_conn()
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT * FROM messages WHERE category = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT * FROM messages ORDER BY created_at DESC LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_alerts(self, is_handled: int = None) -> List[Dict]:
        """获取预警列表"""
        conn = self._get_conn()
        cursor = conn.cursor()

        if is_handled is not None:
            cursor.execute('''
                SELECT a.*, m.content, m.sender_name
                FROM alerts a JOIN messages m ON a.message_id = m.id
                WHERE a.is_handled = ?
                ORDER BY a.created_at DESC
            ''', (is_handled,))
        else:
            cursor.execute('''
                SELECT a.*, m.content, m.sender_name
                FROM alerts a JOIN messages m ON a.message_id = m.id
                ORDER BY a.created_at DESC
            ''')

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def handle_alert(self, alert_id: int, handled_by: str):
        """处理预警"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE alerts SET is_handled = 1, handled_by = ?, handled_at = ?
            WHERE id = ?
        ''', (handled_by, datetime.now(), alert_id))
        conn.commit()
        conn.close()

    def get_stats(self, days: int = 7) -> Dict:
        """获取统计数据"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # 按分类统计
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM messages
            WHERE created_at >= datetime('now', ?)
            GROUP BY category
        ''', (f'-{days} days',))
        category_stats = {row['category']: row['count'] for row in cursor.fetchall()}

        # 按天统计
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM messages
            WHERE created_at >= datetime('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (f'-{days} days',))
        daily_stats = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]

        # 预警统计
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_handled = 1 THEN 1 ELSE 0 END) as handled
            FROM alerts
            WHERE created_at >= datetime('now', ?)
        ''', (f'-{days} days',))
        alert_row = cursor.fetchone()
        alert_stats = dict(alert_row) if alert_row else {'total': 0, 'handled': 0}

        conn.close()
        return {
            'category_stats': category_stats,
            'daily_stats': daily_stats,
            'alert_stats': alert_stats
        }


# 全局实例
db = Database()
