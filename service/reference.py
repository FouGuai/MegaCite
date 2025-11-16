def generate_cid(title: str, source_url: str) -> str:
    """
    根据 title 与 source_url 生成永久 CID（返回 str）。
    说明: 算法内部决定，外部仅使用返回的字符串。
    """

def register_cid(cid: str, path: str, storage_ref: str) -> bool:
    """
    将 cid 与当前 path/storage_ref 登记（请求持久化层保存）。
    - cid: str
    - path: str (可变地址)
    - storage_ref: str (如文件路径)
    返回 True/False
    说明: 本函数应调用 zhengdongze_storage.save_cid_mapping(...)（由郑东泽实现）
    """

def lookup_cid(cid: str) -> dict:
    """
    查询 cid 映射并返回 dict:
    {
      "cid": str,
      "path": str,
      "storage_ref": str,
      "last_updated": str  # ISO 时间字符串
    }
    或返回 {} 表示未找到。
    """

def resolve_cid_for_access(cid: str) -> str:
    """
    返回供外部访问的最终 URL/path（字符串），或 "" 表示不可用。
    说明: 仅做解析决策，持久化/读写由 zhengdongze_storage 提供。
    """
