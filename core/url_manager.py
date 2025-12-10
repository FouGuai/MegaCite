import urllib.parse

class URLManager:
    """
    负责将 CID 映射到 'username/safe_title' 格式的相对路径（不含后缀）。
    """
    _instance = None
    
    # 双向映射
    _cid_to_relpath: dict[str, str] = {}
    _relpath_to_cid: dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(URLManager, cls).__new__(cls)
        return cls._instance

    def safe_title(self, title: str) -> str:
        """
        将标题转换为 URL 安全字符串。
        1. 替换文件系统非法字符（如 / \）
        2. 进行 URL 编码（确保空格等字符在浏览器中合法）
        """
        if not title:
            return "untitled"
        
        # 预处理：将路径分隔符替换为连字符，避免生成多级目录
        safe_str = title.replace("/", "-").replace("\\", "-")
        
        # URL 编码：例如 "Hello World" -> "Hello%20World"
        # 这样生成的物理文件名也会包含 %20，浏览器直接访问即可
        return urllib.parse.quote(safe_str)

    def register_mapping(self, cid: str, username: str, title: str) -> str:
        """
        注册映射，返回相对路径前缀。
        Return: "username/EncodedTitle"
        """
        rel_path = f"{username}/{self.safe_title(title)}"
        
        # 更新映射，处理旧路径残留
        old_path = self._cid_to_relpath.get(cid)
        if old_path and old_path != rel_path:
            if old_path in self._relpath_to_cid:
                del self._relpath_to_cid[old_path]
        
        self._cid_to_relpath[cid] = rel_path
        self._relpath_to_cid[rel_path] = cid
        return rel_path

    def remove_mapping(self, cid: str) -> str | None:
        path = self._cid_to_relpath.pop(cid, None)
        if path and path in self._relpath_to_cid:
            del self._relpath_to_cid[path]
        return path