"""
DeepInsight SQLite 数据库管理器
支持多租户数据隔离，所有操作都需要 username 进行数据隔离
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager


DATABASE_FILE = "deepinsight.db"


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """初始化数据库表结构"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                topic TEXT NOT NULL,
                action_queue TEXT DEFAULT '[]',
                business_assets TEXT DEFAULT '{}',
                evaluation_report TEXT DEFAULT '',
                director_outline TEXT DEFAULT '',
                anchor_output TEXT DEFAULT '',
                raw_script TEXT DEFAULT '',
                messages TEXT DEFAULT '[]',
                tutor_messages TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_username ON live_records(username)
        """)
        conn.commit()


def save_live_record(
    username: str,
    topic: str,
    action_queue: List[Dict] = None,
    business_assets: Dict = None,
    evaluation_report: str = "",
    director_outline: str = "",
    anchor_output: str = "",
    raw_script: str = "",
    messages: List[Dict] = None,
    tutor_messages: List[Dict] = None
) -> int:
    """
    保存直播记录（新增或更新）
    数据隔离：只保存当前用户的数据
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        action_queue_json = json.dumps(action_queue or [], ensure_ascii=False)
        business_assets_json = json.dumps(business_assets or {}, ensure_ascii=False)
        messages_json = json.dumps(messages or [], ensure_ascii=False)
        tutor_messages_json = json.dumps(tutor_messages or [], ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO live_records (
                username, topic, action_queue, business_assets, evaluation_report,
                director_outline, anchor_output, raw_script, messages, tutor_messages,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, topic, action_queue_json, business_assets_json, evaluation_report,
            director_outline, anchor_output, raw_script, messages_json, tutor_messages_json,
            now, now
        ))
        
        conn.commit()
        return cursor.lastrowid


def update_live_record(
    username: str,
    record_id: int,
    **kwargs
) -> bool:
    """
    更新直播记录
    数据隔离：必须验证 username 确保只能修改自己的记录
    """
    if not kwargs:
        return False
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM live_records WHERE id = ? AND username = ?", (record_id, username))
        if not cursor.fetchone():
            return False
        
        allowed_fields = {
            'topic', 'action_queue', 'business_assets', 'evaluation_report',
            'director_outline', 'anchor_output', 'raw_script', 'messages', 'tutor_messages'
        }
        
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if key not in allowed_fields:
                continue
            
            if key in ('action_queue', 'business_assets', 'messages', 'tutor_messages'):
                value = json.dumps(value, ensure_ascii=False) if value else '[]'
            
            updates.append(f"{key} = ?")
            values.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        values.append(record_id)
        values.append(username)
        
        query = f"UPDATE live_records SET {', '.join(updates)} WHERE id = ? AND username = ?"
        cursor.execute(query, values)
        conn.commit()
        
        return cursor.rowcount > 0


def get_user_records(username: str, limit: int = 50) -> List[Dict]:
    """
    获取用户的所有直播记录
    数据隔离：只返回当前用户的记录
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM live_records 
            WHERE username = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (username, limit))
        
        rows = cursor.fetchall()
        results = []
        
        for row in rows:
            record = dict(row)
            record['action_queue'] = json.loads(record['action_queue'] or '[]')
            record['business_assets'] = json.loads(record['business_assets'] or '{}')
            record['messages'] = json.loads(record['messages'] or '[]')
            record['tutor_messages'] = json.loads(record['tutor_messages'] or '[]')
            results.append(record)
        
        return results


def get_record_by_id(username: str, record_id: int) -> Optional[Dict]:
    """
    根据 ID 获取单条记录
    数据隔离：必须验证 username
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM live_records 
            WHERE id = ? AND username = ?
        """, (record_id, username))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        record = dict(row)
        record['action_queue'] = json.loads(record['action_queue'] or '[]')
        record['business_assets'] = json.loads(record['business_assets'] or '{}')
        record['messages'] = json.loads(record['messages'] or '[]')
        record['tutor_messages'] = json.loads(record['tutor_messages'] or '[]')
        
        return record


def delete_record(username: str, record_id: int) -> bool:
    """
    删除指定记录
    数据隔离：只能删除自己的记录
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM live_records 
            WHERE id = ? AND username = ?
        """, (record_id, username))
        conn.commit()
        return cursor.rowcount > 0


def get_record_count(username: str) -> int:
    """获取用户总记录数"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM live_records WHERE username = ?", (username,))
        return cursor.fetchone()[0]


if __name__ == "__main__":
    init_database()
    print("数据库初始化完成！")
