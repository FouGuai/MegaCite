import urllib.parse
import re

class URLManager:
    """
    负责路径映射。
    策略：强制 Slug 化，将空格和特殊字符转换为连字符，确保文件名干净且可读。
    """
    _instance = None
    _cid_map: dict[str, str] = {} # cid -> rel_path

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(URLManager, cls).__new__(cls)
        return cls._instance

    def safe_title(self, title: str) -> str:
        """
        生成 URL 安全标题 (Slug)。
        Example: "Hello World" -> "Hello-World"
        """
        if not title:
            return "untitled"
        
        # 1. 去除首尾空格
        safe = title.strip()
        
        # 2. 将空格、斜杠、反斜杠替换为连字符
        safe = safe.replace(" ", "-").replace("/", "-").replace("\\", "-")
        
        # 3. 移除多余的连字符 (e.g. "Hello--World" -> "Hello-World")
        while "--" in safe:
            safe = safe.replace("--", "-")
            
        # 4. URL 编码 (处理中文等非 ASCII 字符)
        return urllib.parse.quote(safe)

    def register_mapping(self, cid: str, username: str, title: str) -> str:
        """返回相对路径前缀: username/safe-title"""
        rel_path = f"{username}/{self.safe_title(title)}"
        self._cid_map[cid] = rel_path
        return rel_path

    def remove_mapping(self, cid: str) -> str | None:
        return self._cid_map.pop(cid, None)