import urllib.parse
from core.config import SERVER_CONFIG
from dao.factory import create_connection
from dao.url_map_dao import MySQLUrlMapDAO

class URLManager:
    """
    负责路径映射和 URL 解析。
    """
    _instance = None
    _cid_map: dict[str, str] = {} # cid -> rel_path

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(URLManager, cls).__new__(cls)
        return cls._instance

    def safe_title(self, title: str) -> str:
        """生成 URL 安全标题 (Slug)。"""
        if not title:
            return "untitled"
        
        safe = title.strip()
        safe = safe.replace(" ", "-").replace("/", "-").replace("\\", "-")
        while "--" in safe:
            safe = safe.replace("--", "-")
        return urllib.parse.quote(safe)

    def register_mapping(self, cid: str, username: str, title: str) -> str:
        """返回相对路径前缀: username/safe-title"""
        rel_path = f"{username}/{self.safe_title(title)}"
        self._cid_map[cid] = rel_path
        return rel_path

    def remove_mapping(self, cid: str) -> str | None:
        return self._cid_map.pop(cid, None)

    def get_cid_from_external_url(self, url: str) -> str | None:
        """
        解析外界传入的完整 URL，返回对应的 CID。
        """
        try:
            parsed = urllib.parse.urlparse(url)
        except ValueError:
            return None
        
        # 1. 验证域名和端口
        expected_netloc = f"{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}"
        if parsed.netloc != expected_netloc:
            return None
            
        # 2. 提取路径 (严格匹配)
        url_path = parsed.path
        
        # 3. 查库
        conn = create_connection()
        try:
            map_dao = MySQLUrlMapDAO(conn)
            return map_dao.get_cid_by_url(url_path)
        finally:
            conn.close()