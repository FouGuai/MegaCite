from typing import Any
from dao.database import MySQLPostDAO
from services.db import create_connection
from services.auth_service import verify_token

def post_list(token: str, count: int | None = None) -> list[str]:
    """
    列出文章 CID。
    对应 CLI: mc post list [<count>]
    """
    # 验证身份
    verify_token(token)
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        limit = count if count is not None else 100 # 默认限制 100 条
        return dao.list_posts(offset=0, limit=limit)
    finally:
        conn.close()

def post_create(token: str, cid: str) -> None:
    """
    创建文章。
    对应 CLI: mc post create <cid>
    """
    user_id = verify_token(token)
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        # 日期参数传 None，让 DAO 处理为当前日期
        dao.create_post(owner_id=user_id, cid=cid, date=None)
    finally:
        conn.close()

def post_update(token: str, cid: str, field: str, value: str) -> bool:
    """
    更新文章字段。
    对应 CLI: mc post update <cid> <field> <value>
    """
    verify_token(token)
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.update_field(cid, field, value)
    finally:
        conn.close()

def post_delete(token: str, cid: str) -> bool:
    """
    删除文章。
    对应 CLI: mc post delete <cid>
    """
    verify_token(token)
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.delete_post(cid)
    finally:
        conn.close()

def post_get(token: str, cid: str, field: str) -> Any:
    """
    获取文章字段内容。
    对应 CLI: mc post get <cid> <field>
    """
    verify_token(token)
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.get_field(cid, field)
    finally:
        conn.close()

def post_search(token: str, keyword: str) -> list[str]:
    """
    搜索文章。
    对应 CLI: mc post search <keyword>
    """
    verify_token(token)
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.search_posts(keyword)
    finally:
        conn.close()