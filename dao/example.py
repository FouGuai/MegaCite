"""示例脚本：演示如何使用本地 MySQL（`127.0.0.1:3306`）和库中所有 DAO 函数。

请根据你的环境替换连接信息（user/password/database）。
运行: `python dao/example_usage.py`
"""
import os
from database import (
    get_mysql_connection,
    MySQLUserDAO,
    MySQLAuthDAO,
    MySQLPostDAO,
    MySQLPostReferenceDAO,
)


def main():
    # 本示例使用本地 IP 和通用端口 3306。请替换为你的 MySQL 凭据。
    conn = get_mysql_connection(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="114514",
        database="megacite",
    )

    try:
        # 实例化 DAO
        user_dao = MySQLUserDAO(conn)
        auth_dao = MySQLAuthDAO(conn)
        post_dao = MySQLPostDAO(conn)
        ref_dao = MySQLPostReferenceDAO(conn)

        # ---------- UserDAO 示例 ----------
        print("== UserDAO 示例 ==")
        user_id = user_dao.create_user("alice", "hashed_pw_alice")
        print("create_user ->", user_id)

        user = user_dao.get_user_by_username("alice")
        print("get_user_by_username ->", user)

        updated = user_dao.update_user(user_id, {"token": "tok123"})
        print("update_user ->", updated)

        # ---------- AuthDAO 示例 ----------
        print("\n== AuthDAO 示例 ==")
        auth_dao.add_platform_auth(user_id, "csdn", "csdn_token_abc")
        print("add_platform_auth -> done")

        platforms = auth_dao.list_platform_auths(user_id)
        print("list_platform_auths ->", platforms)

        cred = auth_dao.get_platform_credential(user_id, "csdn")
        print("get_platform_credential ->", cred)

        removed = auth_dao.remove_platform_auth(user_id, "csdn")
        print("remove_platform_auth ->", removed)

        # Re-add to continue demo
        auth_dao.add_platform_auth(user_id, "csdn", "csdn_token_abc")

        # ---------- PostDAO 示例 ----------
        print("\n== PostDAO 示例 ==")
        cid1 = "post-cid-1"
        post_dao.create_post(user_id, cid1)  # 使用当前日期
        print("create_post ->", cid1)

        # 更新单个字段（按 DataInterface 文档）
        post_dao.update_field(cid1, "title", "Hello World")
        post_dao.update_field(cid1, "description", "A simple post")
        post_dao.update_field(cid1, "context", "本文正文...")
        print("update_field -> title/description/context updated")

        title = post_dao.get_field(cid1, "title")
        print("get_field(title) ->", title)

        cids = post_dao.list_posts(0, 10)
        print("list_posts ->", cids)

        matches = post_dao.search_posts("Hello")
        print("search_posts('Hello') ->", matches)

        # 创建第二篇文章示例用于引用
        cid2 = "post-cid-2"
        post_dao.create_post(user_id, cid2)
        post_dao.update_field(cid2, "title", "Referenced Post")

        # ---------- PostReferenceDAO 示例 ----------
        print("\n== PostReferenceDAO 示例 ==")
        ref_dao.add_reference(cid1, cid2)
        print("add_reference ->", cid1, "->", cid2)

        refs = ref_dao.list_references(cid1)
        print("list_references ->", refs)

        ref_dao.remove_reference(cid1, cid2)
        print("remove_reference -> done")

        # 清理示例数据
        print("\n== 清理示例数据 ==")
        deleted_post1 = post_dao.delete_post(cid1)
        deleted_post2 = post_dao.delete_post(cid2)
        print("delete_post ->", deleted_post1, deleted_post2)

        deleted_user = user_dao.delete_user(user_id)
        print("delete_user ->", deleted_user)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
