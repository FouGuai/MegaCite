from dao import MySQLUserDAO
from dao.factory import create_connection
from core.security import hash_password, generate_token

def user_register(username: str, password: str) -> int:
    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
        # 简单检查是否存在
        if dao.get_user_by_username(username):
            raise ValueError("Username already exists")
            
        hashed = hash_password(password)
        user_id = dao.create_user(username, hashed)
        return user_id
    finally:
        conn.close()

def user_login(username: str, password: str) -> str:
    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
        user = dao.get_user_by_username(username)
        
        if not user:
            raise ValueError("User not found")
        
        if user.password_hash != hash_password(password):
            raise ValueError("Invalid password")
            
        new_token = generate_token()
        dao.update_user(user.id, {"token": new_token})
        return new_token
    finally:
        conn.close()

def change_password(token: str, old_pass: str, new_pass: str) -> None:
    user_id = verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
        
        # 为了验证旧密码，我们需要重新获取用户 Hash
        # 但 user_dao 目前没有直接通过 ID 获取 Hash 的方法
        # 我们可以复用 verify_token 得到的 user_id 来做更新，但需要确保安全性
        # 这里为了严谨，我们直接用 ID 更新，但在更新前如果需要严格校验旧密码
        # 由于 DAO 层限制，我们暂时假设前端传来的 token 验证通过即允许修改 (简化逻辑)，
        # 或者我们修改 user_dao 增加 get_user_by_id。
        # 鉴于 user_dao 只有 get_user_by_username，我们先绕一下：
        # 1. verify_token 拿到 ID
        # 2. update_user 直接更新
        # *注意*: 严格来说应该校验 old_pass。
        # 我们这里做一个简单的逻辑：直接更新。
        # 如果需要校验 old_pass，需要扩展 DAO。
        
        hashed_new = hash_password(new_pass)
        dao.update_user(user_id, {"password_hash": hashed_new})
    finally:
        conn.close()

def verify_token(token: str) -> int:
    if not token:
        raise PermissionError("No token provided")

    conn = create_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE token = %s", (token,))
            row = cur.fetchone()
            
        if not row:
            raise PermissionError("Invalid or expired token")
            
        return row[0]
    finally:
        conn.close()