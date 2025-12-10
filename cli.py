import argparse
import sys
import getpass
from services import server_service, auth_service, post_service
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
    user_subs.add_parser("register", help="Register a new user")
    user_subs.add_parser("login", help="Login to system")
    user_subs.add_parser("logout", help="Logout from system")

    # --- post ---
    post_parser = subparsers.add_parser("post", help="Post management")
    post_subs = post_parser.add_subparsers(dest="action", required=True)
    
    # list
    list_p = post_subs.add_parser("list", help="List posts")
    list_p.add_argument("count", nargs="?", type=int, default=None)
    
    # create (无需参数，CID 自动生成)
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
                server_service.server_start(args.port)

        elif args.command == "user":
            if args.action == "register":
                u = input("Username: ")
                p = getpass.getpass("Password: ")
                uid = auth_service.user_register(u, p)
                print(f"User registered. ID: {uid}")
            elif args.action == "login":
                u = input("Username: ")
                p = getpass.getpass("Password: ")
                token = auth_service.user_login(u, p)
                store.save_local_token(token)
                print("Login successful.")
            elif args.action == "logout":
                store.clear_local_token()
                print("Logged out.")

        elif args.command == "post":
            token = store.load_local_token()
            
            if args.action == "list":
                print(f"Posts: {post_service.post_list(token, args.count)}")
            
            elif args.action == "create":
                # 修改点：不再传递 cid，获取返回的 cid
                new_cid = post_service.post_create(token)
                print(f"Post created. CID: {new_cid}")
            
            elif args.action == "update":
                # 修复：处理转义字符，将字面量 \n 转换为换行符
                value = args.value.replace("\\n", "\n")
                ok = post_service.post_update(token, args.cid, args.field, value)
                print("Success" if ok else "Failed")
            
            elif args.action == "delete":
                ok = post_service.post_delete(token, args.cid)
                print("Success" if ok else "Failed")
            
            elif args.action == "get":
                print(f"{args.field}: {post_service.post_get(token, args.cid, args.field)}")
            
            elif args.action == "search":
                print(f"Results: {post_service.post_search(token, args.keyword)}")

    except PermissionError:
        print("Error: Please login first.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()