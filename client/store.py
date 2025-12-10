import os
from pathlib import Path

# 定义本地 Token 存储路径，通常在用户主目录下
TOKEN_FILE = Path.home() / ".megacite_token"

def save_local_token(token: str) -> None:
    """
    将 Token 保存到本地文件。
    """
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(token)

def load_local_token() -> str | None:
    """
    从本地文件读取 Token。如果文件不存在则返回 None。
    """
    if not TOKEN_FILE.exists():
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None

def clear_local_token() -> None:
    """
    删除本地 Token 文件。
    """
    if TOKEN_FILE.exists():
        os.remove(TOKEN_FILE)