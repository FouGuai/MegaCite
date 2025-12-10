import pymysql.connections
from .models import User

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

    def get_user_by_username(self, username: str) -> User | None:
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

    def update_user(self, user_id: int, updates: dict[str, any]) -> bool:
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