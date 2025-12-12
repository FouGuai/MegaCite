from verification.csdn import CSDNVerifier
from verification.jianshu import JianshuVerifier
from verification.cnblogs import CNBlogsVerifier
from verification.juejin import JuejinVerifier
from verification.yuque import YuqueVerifier
from client.cookie_store import save_cookies
from dao.factory import create_connection
from dao.auth_dao import MySQLAuthDAO
import json
import uuid
from threading import Lock
from time import time

# 内存会话存储
_sessions = {}
_sessions_lock = Lock()


class VerificationSession:
    """验证会话"""
    def __init__(self, session_id: str, user_id: int, platform: str):
        self.session_id = session_id
        self.user_id = user_id
        self.platform = platform
        self.created_at = time()
        self.status = "pending"  # pending, authenticated, failed
        self.error_message = None


def _get_verifier(platform_or_url: str):
    target = platform_or_url.lower()
    
    # CSDN 匹配
    if target == "csdn" or "csdn.net" in target:
        return CSDNVerifier()
    
    # 简书 匹配
    if target == "jianshu" or "jianshu.com" in target:
        return JianshuVerifier()

    # 博客园 匹配
    if target == "cnblogs" or "cnblogs.com" in target:
        return CNBlogsVerifier()

    # 掘金 匹配
    if target == "juejin" or "juejin.cn" in target:
        return JuejinVerifier()

    # 语雀 匹配
    if target == "yuque" or "yuque.com" in target:
        return YuqueVerifier()
        
    return None

def login_platform(platform_name: str) -> bool:
    verifier = _get_verifier(platform_name)
    if not verifier:
        print(f"[-] Platform '{platform_name}' not supported.")
        return False
    return verifier.login()

def verify_url_owner(url: str) -> bool:
    verifier = _get_verifier(url)
    if not verifier:
        print(f"[-] No verifier found for URL: {url}")
        print("[-] Blind crawling is prohibited. Please implement a verifier for this platform.")
        return False
    
    return verifier.check_ownership(url)


# ========== 会话管理 APIs ==========

def session_init(user_id: int, platform: str) -> str:
    """初始化验证会话，返回 session_id"""
    if not _get_verifier(platform):
        raise ValueError(f"Platform '{platform}' not supported")
    
    session_id = str(uuid.uuid4())
    session = VerificationSession(session_id, user_id, platform)
    
    with _sessions_lock:
        _sessions[session_id] = session
    
    return session_id


def session_save_cookies(session_id: str, cookies: list) -> bool:
    """保存验证后的 Cookies"""
    with _sessions_lock:
        session = _sessions.get(session_id)
        if not session:
            return False
    
    # 保存到本地 Cookie 存储
    save_cookies(session.platform, cookies)
    
    # 保存到数据库
    try:
        conn = create_connection()
        dao = MySQLAuthDAO(conn)
        credential = json.dumps(cookies)
        dao.add_platform_auth(session.user_id, session.platform, credential)
        conn.close()
    except Exception as e:
        print(f"[-] Failed to save to database: {e}")
    
    # 更新会话状态
    with _sessions_lock:
        session.status = "authenticated"
    
    return True


def session_get_status(session_id: str) -> dict:
    """获取会话状态"""
    with _sessions_lock:
        session = _sessions.get(session_id)
    
    if not session:
        return {"status": "invalid"}
    
    return {
        "status": session.status,
        "platform": session.platform,
        "error": session.error_message,
    }


def session_close(session_id: str):
    """关闭会话"""
    with _sessions_lock:
        if session_id in _sessions:
            del _sessions[session_id]


def session_save_error(session_id: str, error_message: str):
    """保存验证错误"""
    with _sessions_lock:
        session = _sessions.get(session_id)
        if not session:
            return False
        session.status = "failed"
        session.error_message = error_message
    return True