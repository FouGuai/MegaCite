import pymysql
import pymysql.cursors

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