from datetime import datetime
import pymysql.connections

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

    def get_field(self, cid: str, field: str) -> any:
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

    def list_posts(self, offset: int, limit: int, orderby=None) -> list[str]:
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

    def search_posts(self, keyword: str) -> list[str]:
        """按关键字搜索文章，优先级：title > description > context，返回匹配到的 CID 列表（去重，按优先级排序）。"""
        like = f"%{keyword}%"
        results: list[str] = []
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