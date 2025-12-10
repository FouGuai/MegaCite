from typing import Any
from dao.database import MySQLPostDAO
from services.db import create_connection
from services.auth_service import verify_token
from core.security import generate_cid

def post_list(token: str, count: int | None = None) -> list[str]:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        limit = count if count is not None else 100
        return dao.list_posts(offset=0, limit=limit)
    finally:
        conn.close()

def post_create(token: str) -> str:
    """
    创建文章，自动生成 CID。
    Returns: 新生成的 CID
    """
    user_id = verify_token(token)
    
    # 生成唯一 CID
    new_cid = generate_cid()
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        dao.create_post(owner_id=user_id, cid=new_cid, date=None)
        return new_cid
    finally:
        conn.close()

def post_update(token: str, cid: str, field: str, value: str) -> bool:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.update_field(cid, field, value)
    finally:
        conn.close()

def post_delete(token: str, cid: str) -> bool:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.delete_post(cid)
    finally:
        conn.close()

def post_get(token: str, cid: str, field: str) -> Any:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.get_field(cid, field)
    finally:
        conn.close()

def post_search(token: str, keyword: str) -> list[str]:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.search_posts(keyword)
    finally:
        conn.close()