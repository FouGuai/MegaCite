import hashlib
import uuid

def hash_password(password: str) -> str:
    """
    对密码进行 SHA256 哈希处理。
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def generate_token() -> str:
    """
    生成一个随机的 UUID 作为 Token。
    """
    return uuid.uuid4().hex