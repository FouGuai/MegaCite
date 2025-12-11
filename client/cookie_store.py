import json
import os
from pathlib import Path

COOKIE_FILE = Path.home() / ".megacite_cookies"

def save_cookies(platform: str, cookies: list[dict]) -> None:
    data = {}
    if COOKIE_FILE.exists():
        try:
            with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass

    data[platform] = cookies

    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    
    if os.name == 'posix':
        os.chmod(COOKIE_FILE, 0o600)

def load_cookies(platform: str) -> list[dict] | None:
    if not COOKIE_FILE.exists():
        return None
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(platform)
    except (json.JSONDecodeError, OSError):
        return None

def clear_cookies(platform: str) -> None:
    if not COOKIE_FILE.exists():
        return
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if platform in data:
            del data[platform]
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
    except (json.JSONDecodeError, OSError):
        pass