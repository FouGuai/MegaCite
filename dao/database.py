from dataclasses import dataclass
from datetime import date
from typing import Optional
import pymysql
from typing import List, Optional
from datetime import datetime
from dao_interfaces import UserDAO, AuthDAO, PostDAO, PostReferenceDAO, User
from typing import Any
@dataclass
class User:
    id: int
    username: str
    password_hash: str

@dataclass
class Post:
    cid: str
    owner_id: int
    title: Optional[str]
    context: Optional[str]
    description: Optional[str]
    catagory: Optional[str]
    date: date

from abc import ABC, abstractmethod
from typing import List, Optional


class UserDAO(ABC):

    @abstractmethod
    def create_user(self, username: str, password_hash: str) -> int:
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def update_user(self, user_id: int, dict: dict[str: Any]) -> bool:
        pass

    @abstractmethod 
    def delete_user(self, user_id) -> bool:
        pass


class AuthDAO(ABC):

    @abstractmethod
    def add_platform_auth(self, user_id: int, platform: str, credential: str) -> None:
        pass

    @abstractmethod
    def remove_platform_auth(self, user_id: int, platform: str) -> bool:
        pass

    @abstractmethod
    def list_platform_auths(self, user_id: int) -> List[str]:
        pass

    @abstractmethod
    def get_platform_credential(self, user_id: int, platform: str) -> Optional[str]:
        pass


class PostDAO(ABC):

    @abstractmethod
    def create_post(self, owner_id: int, cid: str, date: str=None) -> None:
        """创建文章，date 自动填入 YYYY-MM-DD 格式"""
        pass

    @abstractmethod
    def update_field(self, cid: str, args : dict[str, Any]) -> bool:
        """field 必须在: context/title/date/description/catagory 内"""
        pass

    @abstractmethod
    def get_field(self, cid: str, field: str) -> Optional[Any]:
        pass

    @abstractmethod
    def delete_post(self, cid: str) -> bool:
        pass

    @abstractmethod
    def list_posts(self, offset: int, limit: int, orderby=None) -> List[str]:
        pass

    @abstractmethod
    def search_posts(self, keyword: str) -> List[str]:
        """命中优先级: title > description > context"""
        pass


class PostReferenceDAO(ABC):

    @abstractmethod
    def add_reference(self, post_cid: str, ref_cid: str) -> None:
        pass

    @abstractmethod
    def remove_reference(self, post_cid: str, ref_cid: str) -> None:
        pass

    @abstractmethod
    def list_references(self, post_cid: str) -> List[str]:
        pass
    

class MySQLBase:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, args=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
        self.conn.commit()

    def query_one(self, sql, args=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

    def query_all(self, sql, args=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()


