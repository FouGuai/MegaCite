from verification.csdn import CSDNVerifier
from verification.jianshu import JianshuVerifier
from verification.cnblogs import CNBlogsVerifier
from verification.juejin import JuejinVerifier

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