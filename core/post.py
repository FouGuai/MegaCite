from typing import Any
from dao import MySQLPostDAO
from dao.factory import create_connection
from logic.auth import verify_token
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
    user_id = verify_token(token)
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