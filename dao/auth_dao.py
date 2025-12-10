import pymysql.connections

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

    def list_platform_auths(self, user_id: int) -> list[str]:
        """返回用户已绑定的平台名称列表。"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT platform FROM auth_platforms WHERE user_id = %s", (user_id,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []

    def get_platform_credential(self, user_id: int, platform: str) -> str | None:
        """获取用户在某平台的凭证，找不到返回 None。"""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT credential FROM auth_platforms WHERE user_id = %s AND platform = %s",
                (user_id, platform),
            )
            row = cur.fetchone()
        return row[0] if row else None