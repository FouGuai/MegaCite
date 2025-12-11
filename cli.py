import argparse
import sys
from core import auth, post
from server import manager as server_manager
from client import store

def main():
    parser = argparse.ArgumentParser(description="MegaCite CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- mc-server ---
    server_parser = subparsers.add_parser("server", help="Server management")
    server_subs = server_parser.add_subparsers(dest="action", required=True)
    start_parser = server_subs.add_parser("start", help="Start the server")
    start_parser.add_argument("port", type=int, help="Port to listen on")

    # --- user ---
    user_parser = subparsers.add_parser("user", help="User management")
    user_subs = user_parser.add_subparsers(dest="action", required=True)
    
    # Register: mc register <username> <password>
    reg_parser = user_subs.add_parser("register", help="Register a new user")
    reg_parser.add_argument("username", help="Username")
    reg_parser.add_argument("password", help="Password")

    # Login: mc login <username> <password>
    login_parser = user_subs.add_parser("login", help="Login to system")
    login_parser.add_argument("username", help="Username")
    login_parser.add_argument("password", help="Password")

    # Logout
    user_subs.add_parser("logout", help="Logout from system")

    # --- post ---
    post_parser = subparsers.add_parser("post", help="Post management")
    post_subs = post_parser.add_subparsers(dest="action", required=True)
    
    # list
    list_p = post_subs.add_parser("list", help="List posts")
    list_p.add_argument("count", nargs="?", type=int, default=None)
    
    # create
    post_subs.add_parser("create", help="Create a post")
    
    # update
    update_p = post_subs.add_parser("update", help="Update post")
    update_p.add_argument("cid")
    update_p.add_argument("field", choices=["title", "context", "description", "catagory", "date"])
    update_p.add_argument("value")
    
    # delete
    delete_p = post_subs.add_parser("delete", help="Delete post")
    delete_p.add_argument("cid")
    
    # get
    get_p = post_subs.add_parser("get", help="Get field")
    get_p.add_argument("cid")
    get_p.add_argument("field")
    
    # search
    search_p = post_subs.add_parser("search", help="Search")
    search_p.add_argument("keyword")

    args = parser.parse_args()

    try:
        if args.command == "server":
            if args.action == "start":
                server_manager.server_start(args.port)

        elif args.command == "user":
            if args.action == "register":
                # 直接使用位置参数
                uid = auth.user_register(args.username, args.password)
                print(f"User registered. ID: {uid}")
            elif args.action == "login":
                # 直接使用位置参数
                token = auth.user_login(args.username, args.password)
                store.save_local_token(token)
                print("Login successful.")
            elif args.action == "logout":
                store.clear_local_token()
                print("Logged out.")

        elif args.command == "post":
            token = store.load_local_token()
            
            if args.action == "list":
                print(f"Posts: {post.post_list(token, args.count)}")
            
            elif args.action == "create":
                new_cid = post.post_create(token)
                print(f"Post created. CID: {new_cid}")
            
            elif args.action == "update":
                # 处理转义字符
                value = args.value.replace("\\n", "\n")
                ok = post.post_update(token, args.cid, args.field, value)
                print("Success" if ok else "Failed")
            
            elif args.action == "delete":
                ok = post.post_delete(token, args.cid)
                print("Success" if ok else "Failed")
            
            elif args.action == "get":
                print(f"{args.field}: {post.post_get(token, args.cid, args.field)}")
            
            elif args.action == "search":
                print(f"Results: {post.post_search(token, args.keyword)}")

    except PermissionError:
        print("Error: Please login first.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()