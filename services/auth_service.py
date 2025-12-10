from dao.database import MySQLUserDAO
from services.db import create_connection
from core.security import hash_password, generate_token

def user_register(username: str, password: str) -> int:
    """
    注册新用户。
    返回: 新用户的 ID。
    """
    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
        hashed = hash_password(password)
        # 注意：这里可能会抛出 pymysql.IntegrityError (如用户名重复)，由 CLI 层捕获
        user_id = dao.create_user(username, hashed)
        return user_id
    finally:
        conn.close()

def user_login(username: str, password: str) -> str:
    """
    用户登录。
    验证成功后生成新 Token 并存入数据库。
    返回: Token 字符串。
    """
    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
        user = dao.get_user_by_username(username)
        
        if not user:
            raise ValueError("User not found")
        
        # 验证密码
        if user.password_hash != hash_password(password):
            raise ValueError("Invalid password")
            
        # 生成并更新 Token
        new_token = generate_token()
        dao.update_user(user.id, {"token": new_token})
        return new_token
    finally:
        conn.close()

def verify_token(token: str) -> int:
    """
    验证 Token 的有效性。
    逻辑: Token 不能为空，且必须在数据库中存在对应的用户。
    返回: 对应的 user_id。
    异常: PermissionError (如果 Token 无效)。
    """
    if not token:
        raise PermissionError("No token provided")

    conn = create_connection()
    try:
        # UserDAO 没有直接通过 token 查找的方法，我们需要直接用 SQL 查
        # 或者遍历用户（效率低，不推荐）。
        # 此处为了性能，直接使用 cursor 查询 user_id
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE token = %s", (token,))
            row = cur.fetchone()
            
        if not row:
            raise PermissionError("Invalid or expired token")
            
        return row[0]
    finally:
        conn.close()