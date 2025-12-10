import socket
from services.db import create_connection

def server_start(port: int) -> None:
    """
    启动服务（模拟）。
    实际上只检查数据库连接并监听端口以模拟服务启动状态。
    """
    print(f"[*] Initializing MegaCite server on port {port}...")
    
    # 1. 检查数据库连接
    try:
        conn = create_connection()
        conn.ping()
        print("[+] Database connection successful.")
        conn.close()
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    # 2. 模拟启动监听
    try:
        # 创建一个简单的 socket 监听来模拟服务占用端口
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(1)
        print(f"[+] Server started successfully. Listening on 0.0.0.0:{port}")
        print("[*] Press Ctrl+C to stop.")
        
        while True:
            # 阻塞进程，模拟守护进程
            conn, addr = server_socket.accept()
            conn.close()
    except KeyboardInterrupt:
        print("\n[*] Server stopping...")
    except Exception as e:
        print(f"[-] Server error: {e}")
    finally:
        try:
            server_socket.close()
        except UnboundLocalError:
            pass