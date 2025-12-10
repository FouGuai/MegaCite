import pymysql.connections

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

    def list_references(self, post_cid: str) -> list[str]:
        """列出某篇文章的所有引用 CID 列表。"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT ref_cid FROM post_references WHERE post_cid = %s", (post_cid,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []