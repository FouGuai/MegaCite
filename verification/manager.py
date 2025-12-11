from verification.csdn import CSDNVerifier
from verification.jianshu import JianshuVerifier
from verification.cnblogs import CNBlogsVerifier
from verification.juejin import JuejinVerifier
from verification.yuque import YuqueVerifier

_active_verifier = None

def _get_verifier(platform_or_url: str):
    target = platform_or_url.lower()
    if target == "csdn" or "csdn.net" in target: return CSDNVerifier()
    if target == "jianshu" or "jianshu.com" in target: return JianshuVerifier()
    if target == "cnblogs" or "cnblogs.com" in target: return CNBlogsVerifier()
    if target == "juejin" or "juejin.cn" in target: return JuejinVerifier()
    if target == "yuque" or "yuque.com" in target: return YuqueVerifier()
    return None

def login_platform(platform_name: str) -> bool:
    v = _get_verifier(platform_name)
    if v: return v.login()
    return False

def verify_url_owner(url: str) -> bool:
    v = _get_verifier(url)
    if v: return v.check_ownership(url)
    return False

def session_start(platform_name: str) -> bool:
    global _active_verifier
    session_close()
    verifier = _get_verifier(platform_name)
    if not verifier: return False
    try:
        verifier.start_login_session()
        _active_verifier = verifier
        return True
    except Exception as e:
        print(f"[-] Session Start Error: {e}")
        return False

def session_get_screenshot() -> str | None:
    global _active_verifier
    if _active_verifier: return _active_verifier.get_login_screenshot()
    return None

def session_handle_interaction(action: str, payload: dict) -> None:
    global _active_verifier
    if _active_verifier:
        _active_verifier.handle_interaction(action, payload)

def session_check_status() -> bool:
    global _active_verifier
    if _active_verifier:
        success = _active_verifier.check_login_status()
        if success:
            session_close()
            return True
    return False

def session_close() -> None:
    global _active_verifier
    if _active_verifier:
        _active_verifier.close_session()
        _active_verifier = None