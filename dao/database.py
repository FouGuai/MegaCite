from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, List, Optional
import pymysql
import pymysql.cursors
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


def get_mysql_connection(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    charset: str = "utf8mb4",
) -> pymysql.connections.Connection:
    """
    建立并返回一个 pymysql MySQL 连接。

    必要参数: host, port, user, password, database
    可选参数: charset (默认 utf8mb4)

    返回值: 已连接的 `pymysql.connections.Connection` 对象，默认不启用自动提交（调用方可按需 commit/rollback）。
    """
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset=charset,
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False,
    )
    return conn


class MySQLUserDAO:
    """MySQL 实现的 UserDAO。实例化时传入一个已连接的 `pymysql` 连接对象。"""

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def create_user(self, username: str, password_hash: str) -> int:
        """创建新用户并返回生成的 user_id。"""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
            user_id = cur.lastrowid
        self.conn.commit()
        return user_id

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名查询并返回 `User`，找不到返回 `None`。"""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return User(id=row[0], username=row[1], password_hash=row[2])

    def update_user(self, user_id: int, updates: dict[str, Any]) -> bool:
        """部分更新用户字段，返回是否有行被修改。

        示例: `updates={"token": "..."}`
        """
        if not updates:
            return False
        keys = []
        values = []
        for k, v in updates.items():
            keys.append(f"{k} = %s")
            values.append(v)
        values.append(user_id)
        sql = f"UPDATE users SET {', '.join(keys)} WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            changed = cur.rowcount
        self.conn.commit()
        return changed > 0

    def delete_user(self, user_id: int) -> bool:
        """删除用户，返回是否删除成功。"""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            deleted = cur.rowcount
        self.conn.commit()
        return deleted > 0


class MySQLAuthDAO:
    """MySQL 实现的 AuthDAO。实例化时传入一个已连接的 `pymysql` 连接对象。"""

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def add_platform_auth(self, user_id: int, platform: str, credential: str) -> None:
        """为用户添加或更新平台认证凭证（upsert）。"""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO auth_platforms (user_id, platform, credential) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE credential = %s",
                (user_id, platform, credential, credential),
            )
        self.conn.commit()

    def remove_platform_auth(self, user_id: int, platform: str) -> bool:
        """删除指定用户的平台认证，返回是否删除成功。"""
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM auth_platforms WHERE user_id = %s AND platform = %s",
                (user_id, platform),
            )
            deleted = cur.rowcount
        self.conn.commit()
        return deleted > 0

    def list_platform_auths(self, user_id: int) -> List[str]:
        """返回用户已绑定的平台名称列表。"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT platform FROM auth_platforms WHERE user_id = %s", (user_id,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []

    def get_platform_credential(self, user_id: int, platform: str) -> Optional[str]:
        """获取用户在某平台的凭证，找不到返回 None。"""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT credential FROM auth_platforms WHERE user_id = %s AND platform = %s",
                (user_id, platform),
            )
            row = cur.fetchone()
        return row[0] if row else None


class MySQLPostDAO:
    """MySQL 实现的 PostDAO。实例化时传入一个已连接的 `pymysql` 连接对象。

    NOTE: `update_field` 严格按照文档签名: `update_field(self, cid, field, value)`。
    """

    ALLOWED_FIELDS = {"context", "title", "date", "description", "catagory"}

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def create_post(self, owner_id: int, cid: str, date: str = None) -> None:
        """创建一篇文章。`date` 可选，格式为 YYYY-MM-DD；若为空则使用当前日期。"""
        if date is None:
            date = datetime.now().date()
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO posts (cid, owner_id, date) VALUES (%s, %s, %s)",
                (cid, owner_id, date),
            )
        self.conn.commit()

    def update_field(self, cid: str, field: str, value: str) -> bool:
        """更新文章的单个字段（context/title/date/description/catagory），返回是否更新成功。"""
        if field not in self.ALLOWED_FIELDS:
            return False
        sql = f"UPDATE posts SET {field} = %s WHERE cid = %s"
        with self.conn.cursor() as cur:
            cur.execute(sql, (value, cid))
            changed = cur.rowcount
        self.conn.commit()
        return changed > 0

    def get_field(self, cid: str, field: str) -> Optional[Any]:
        """获取文章的单个字段值，找不到或字段非法返回 None。"""
        if field not in self.ALLOWED_FIELDS:
            return None
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT {field} FROM posts WHERE cid = %s", (cid,))
            row = cur.fetchone()
        if not row:
            return None
        return row[0]

    def delete_post(self, cid: str) -> bool:
        """删除文章，返回是否删除成功。"""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM posts WHERE cid = %s", (cid,))
            deleted = cur.rowcount
        self.conn.commit()
        return deleted > 0

    def list_posts(self, offset: int, limit: int, orderby=None) -> List[str]:
        """列出文章 CID 列表，支持简单的 orderby 字段（受白名单保护）。"""
        allowed_order = {"date", "title", "cid", "id"}
        order_clause = "ORDER BY date DESC"
        if orderby in allowed_order:
            order_clause = f"ORDER BY {orderby}"
        sql = f"SELECT cid FROM posts {order_clause} LIMIT %s OFFSET %s"
        with self.conn.cursor() as cur:
            cur.execute(sql, (limit, offset))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []

    def search_posts(self, keyword: str) -> List[str]:
        """按关键字搜索文章，优先级：title > description > context，返回匹配到的 CID 列表（去重，按优先级排序）。"""
        like = f"%{keyword}%"
        results: List[str] = []
        seen = set()

        with self.conn.cursor() as cur:
            cur.execute("SELECT cid FROM posts WHERE title LIKE %s", (like,))
            for r in cur.fetchall():
                cid = r[0]
                if cid not in seen:
                    seen.add(cid)
                    results.append(cid)

            cur.execute("SELECT cid FROM posts WHERE description LIKE %s", (like,))
            for r in cur.fetchall():
                cid = r[0]
                if cid not in seen:
                    seen.add(cid)
                    results.append(cid)

            cur.execute("SELECT cid FROM posts WHERE context LIKE %s", (like,))
            for r in cur.fetchall():
                cid = r[0]
                if cid not in seen:
                    seen.add(cid)
                    results.append(cid)

        return results


class MySQLPostReferenceDAO:
    """MySQL 实现的 PostReferenceDAO。实例化时传入一个已连接的 `pymysql` 连接对象。"""

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def add_reference(self, post_cid: str, ref_cid: str) -> None:
        """为文章添加一条引用关系（忽略已存在的重复）。"""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO post_references (post_cid, ref_cid) VALUES (%s, %s)",
                (post_cid, ref_cid),
            )
        self.conn.commit()

    def remove_reference(self, post_cid: str, ref_cid: str) -> None:
        """删除指定的引用关系。"""
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM post_references WHERE post_cid = %s AND ref_cid = %s",
                (post_cid, ref_cid),
            )
        self.conn.commit()

    def list_references(self, post_cid: str) -> List[str]:
        """列出某篇文章的所有引用 CID 列表。"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT ref_cid FROM post_references WHERE post_cid = %s", (post_cid,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []


