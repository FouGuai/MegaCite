import pymysql.connections

class MySQLPostReferenceDAO:
    """MySQL 实现的 PostReferenceDAO。"""

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def add_reference(self, post_cid: str, ref_cid: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO post_references (post_cid, ref_cid) VALUES (%s, %s)",
                (post_cid, ref_cid),
            )
        self.conn.commit()

    def remove_reference(self, post_cid: str, ref_cid: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM post_references WHERE post_cid = %s AND ref_cid = %s",
                (post_cid, ref_cid),
            )
        self.conn.commit()

    def list_references(self, post_cid: str) -> list[str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT ref_cid FROM post_references WHERE post_cid = %s", (post_cid,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []