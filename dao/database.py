from __future__ import annotations
from typing import Optional, List, Dict
from datetime import datetime
import json


class Article:
    """
    博客内容迁移与引用维护系统 - 文章数据模型

    功能职责：
      - 表示单篇文章的完整数据结构
      - 支持迁移（path可变）、引用维护（cid永不变）
      - 提供基础的引用更新、元数据管理功能
    """

    def __init__(
        self,
        title: str,
        author: str,
        source_url: str,
        references: List[str],
        ref_cnt: int = 0,
        published: Optional[str] = None,
        cid: Optional[str] = None,
        path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
        obj: Optional[Dict[str, str]] = None
    ):
        # 核心内容字段（来自“内容管理”部分）
        self.title: str = title                     # 文章标题
        self.author: str = author                   # 作者名称
        self.source_url: str = source_url           # 原始来源 URL
        self.published: str = published or datetime.now().isoformat()  # 发布时间

        # 引用维护相关字段（来自“引用维护组”部分）
        self.cid: str = cid or ""                   # 永久唯一标识符（CID，不可变）
        self.path: str = path or ""                 # 当前访问路径（可变）
        self.references: List[str] = references or []  # 本文引用的其他文章CID
        self.ref_by: List[str] = ref_by or []          # 被哪些文章引用（反向引用）
        self.cid_map: Dict[str, str] = {}              # CID->URL 映射缓存，用于快速解析

        # 附加信息字段（用于“内容迁移”和“CMS管理”）
        self.tags: List[str] = tags or []
        self.metadata: Dict[str, str] = metadata or {}

        # 状态字段（保证内容资产可靠）
        self.last_modified: str = datetime.now().isoformat()
        self.is_deleted: bool = False
        
        self.obj = obj
    

    # ------------------------------
    # 基础操作方法（对应 CMS 功能）
    # ------------------------------

    def update_path(self, new_path: str) -> None:
        """更新文章 path（URL 变更时调用）"""
        if new_path != self.path:
            self.path = new_path
            self.last_modified = datetime.now().isoformat()

    def add_reference(self, target_cid: str) -> None:
        """向本文添加一个引用（CID形式）"""
        if target_cid not in self.references:
            self.references.append(target_cid)
            self.last_modified = datetime.now().isoformat()

    def remove_reference(self, target_cid: str) -> None:
        """移除一个引用"""
        if target_cid in self.references:
            self.references.remove(target_cid)
            self.last_modified = datetime.now().isoformat()

    def register_cid_mapping(self, cid: str, url: str) -> None:
        """注册或更新一个 CID 对应的 URL 映射（引用维护系统接口调用）"""
        self.cid_map[cid] = url
        self.last_modified = datetime.now().isoformat()

    def get_reference_urls(self) -> List[str]:
        """根据 CID 映射表返回当前引用文章的有效 URL 列表"""
        return [self.cid_map.get(cid, "") for cid in self.references]

    # ------------------------------
    # 序列化方法（用于迁移与持久化）
    # ------------------------------

    def to_dict(self) -> Dict[str, object]:
        """将对象序列化为字典（全部为内建类型）"""
        return {
            "title": self.title,
            "author": self.author,
            "content_html": self.content_html,
            "source_url": self.source_url,
            "published": self.published,
            "cid": self.cid,
            "path": self.path,
            "references": self.references,
            "ref_by": self.ref_by,
            "cid_map": self.cid_map,
            "tags": self.tags,
            "metadata": self.metadata,
            "last_modified": self.last_modified,
            "is_deleted": self.is_deleted
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> Article:
        """从字典反序列化为 Article 对象"""
        return cls(
            title=data.get("title", ""),
            author=data.get("author", ""),
            content_html=data.get("content_html", ""),
            source_url=data.get("source_url", ""),
            published=data.get("published"),
            cid=data.get("cid"),
            path=data.get("path"),
            tags=data.get("tags"),
            references=data.get("references"),
            ref_by=data.get("ref_by"),
            metadata=data.get("metadata")
        )

    def to_json(self) -> str:
        """导出为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> Article:
        """从 JSON 字符串恢复"""
        return cls.from_dict(json.loads(text))

    # ------------------------------
    # 内容状态维护（对应“内容资产完整性”）
    # ------------------------------

    def mark_deleted(self) -> None:
        """标记文章已被作者删除（引用系统需感知）"""
        self.is_deleted = True
        self.last_modified = datetime.now().isoformat()

    def is_valid(self) -> bool:
        """判断文章是否有效（未删除且 CID 已注册）"""
        return not self.is_deleted and bool(self.cid)

    # ------------------------------
    # 调试输出
    # ------------------------------

    def __repr__(self) -> str:
        return f"<Article title={self.title!r}, cid={self.cid}, path={self.path}>"

def save_article_record(artical : Article) -> bool:
    """
    持久化文章记录（record: dict，所有值均为内建类型）。
    record dict {content, obejct}
    自动更新引用关系
    - 返回 True/False
    """

def load_article_record(cid: str) -> Article:
    """
    读取文章记录；若无则返回 {},
    自动更新引用关系
    return dict {content, obejct}
    """

def write_file(file_path: str, data: bytes) -> bool:
    """
    写入二进制静态资源文件（图片/页面），返回 True/False。
    """

def read_file(file_path: str) -> bytes | None:
    """
    读取二进制文件内容；不存在返回 None。
    """

def save_cid_mapping(cid: str, mapping: dict) -> bool:
    """
    保存 CID 映射（mapping 包含 keys: "path","storage_ref","last_updated" 等）。
    """

def load_cid_mapping(cid: str) -> dict:
    """
    加载 CID 映射或返回 {}。
    """
