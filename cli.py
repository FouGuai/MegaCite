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
    
    # post list [count]
    list_p = post_subs.add_parser("list", help="List posts")
    list_p.add_argument("count", nargs="?", type=int, default=None, help="Number of posts")
    
    # post create <cid>
    create_p = post_subs.add_parser("create", help="Create a post")
    create_p.add_argument("cid", help="Content ID")
    
    # post update <cid> <field> <value>
    update_p = post_subs.add_parser("update", help="Update a post field")
    update_p.add_argument("cid", help="Content ID")
    update_p.add_argument("field", choices=["title", "context", "description", "catagory", "date"], help="Field to update")
    update_p.add_argument("value", help="New value")
    
    # post delete <cid>
    delete_p = post_subs.add_parser("delete", help="Delete a post")
    delete_p.add_argument("cid", help="Content ID")
    
    # post get <cid> <field>
    get_p = post_subs.add_parser("get", help="Get post field")
    get_p.add_argument("cid", help="Content ID")
    get_p.add_argument("field", help="Field name")
    
    # post search <keyword>
    search_p = post_subs.add_parser("search", help="Search posts")
    search_p.add_argument("keyword", help="Search keyword")

    args = parser.parse_args()

    try:
        # === Server Command ===
        if args.command == "server":
            if args.action == "start":
                server_service.server_start(args.port)

        # === User Command ===
        elif args.command == "user":
            if args.action == "register":
                u = input("Username: ")
                p = getpass.getpass("Password: ")
                uid = auth_service.user_register(u, p)
                print(f"User registered successfully. ID: {uid}")
            
            elif args.action == "login":
                u = input("Username: ")
                p = getpass.getpass("Password: ")
                token = auth_service.user_login(u, p)
                store.save_local_token(token)
                print("Login successful. Token saved locally.")
            
            elif args.action == "logout":
                store.clear_local_token()
                print("Logged out.")

        # === Post Command ===
        elif args.command == "post":
            token = store.load_local_token()
            
            if args.action == "list":
                res = post_service.post_list(token, args.count)
                print("Posts:", res)
            
            elif args.action == "create":
                post_service.post_create(token, args.cid)
                print(f"Post {args.cid} created.")
            
            elif args.action == "update":
                ok = post_service.post_update(token, args.cid, args.field, args.value)
                print("Update success" if ok else "Update failed")
            
            elif args.action == "delete":
                ok = post_service.post_delete(token, args.cid)
                print("Delete success" if ok else "Delete failed")
            
            elif args.action == "get":
                res = post_service.post_get(token, args.cid, args.field)
                print(f"{args.field}: {res}")
            
            elif args.action == "search":
                res = post_service.post_search(token, args.keyword)
                print("Search results:", res)

    except PermissionError:
        print("Error: Permission denied. Please login first using 'python cli.py user login'.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()