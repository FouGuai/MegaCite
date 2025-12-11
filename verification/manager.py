from verification.csdn import CSDNVerifier

def _get_verifier(platform_or_url: str):
    target = platform_or_url.lower()
    if target == "csdn" or "csdn.net" in target:
        return CSDNVerifier()
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