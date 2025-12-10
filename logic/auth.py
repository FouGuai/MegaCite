from dao import MySQLUserDAO
from dao.factory import create_connection
from core.security import hash_password, generate_token

def user_register(username: str, password: str) -> int:
    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
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