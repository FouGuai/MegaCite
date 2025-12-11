import time
from dao.factory import create_connection
from dao.reference_dao import MySQLPostReferenceDAO
from generator.builder import StaticSiteGenerator

class DBWatcher:
    """
    后台轮询监听器。
    """
    def __init__(self, generator: StaticSiteGenerator):
        self.gen = generator
        self.running = False
        self._snapshot = {} 

    def _get_current_state(self):
        state = {}
        conn = create_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT cid, owner_id, title, context, description, date, catagory FROM posts")
                rows = cur.fetchall()
                for r in rows:
                    cid, owner_id = r[0], r[1]
                    data_map = {
                        "cid": cid, "owner_id": owner_id, 
                        "title": r[2], "context": r[3], 
                        "description": r[4], "date": str(r[5]), 
                        "catagory": r[6]
                    }
                    # 简单哈希签名用于检测变更
                    sig = hash(tuple(data_map.values()))
                    state[cid] = {"owner_id": owner_id, "data": data_map, "signature": sig}
        finally:
            conn.close()
        return state

    def _get_username(self, user_id):
        conn = create_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
                row = cur.fetchone()
                return row[0] if row else "unknown"
        finally:
            conn.close()

    def _scan(self):
        new_state = self._get_current_state()
        
        # 待更新任务集合：cid -> info
        # 使用字典去重
        tasks = {}
        affected_users = set()

        # 1. 扫描变更
        for cid, info in new_state.items():
            old_info = self._snapshot.get(cid)
            
            # 检测到直接变更 (新增 或 内容变化)
            if not old_info or old_info["signature"] != info["signature"]:
                tasks[cid] = info
                
                # --- 级联更新逻辑 ---
                # 如果是旧文章，且 Title 或 Category 变了 -> URL 变了
                if old_info:
                    old_data = old_info["data"]
                    new_data = info["data"]
                    if old_data["title"] != new_data["title"] or old_data["catagory"] != new_data["catagory"]:
                        print(f"[Watcher] Cascade Trigger: {cid} changed URL structure.")
                        conn = create_connection()
                        try:
                            ref_dao = MySQLPostReferenceDAO(conn)
                            # 找出所有引用了当前文章(cid)的其他文章
                            referencing_cids = ref_dao.get_referencing_posts(cid)
                            print(f"[Watcher] Found referencing posts for {cid}: {referencing_cids}")
                            
                            for ref_cid in referencing_cids:
                                # 如果该文章还存在，且未被列入更新计划，则强制加入
                                if ref_cid in new_state:
                                    if ref_cid not in tasks:
                                        print(f"[Watcher] Cascade Update: Adding {ref_cid} to tasks.")
                                        tasks[ref_cid] = new_state[ref_cid]
                                    else:
                                        print(f"[Watcher] Cascade: {ref_cid} is already in tasks.")
                        finally:
                            conn.close()

        # 2. 扫描删除
        for cid, info in self._snapshot.items():
            if cid not in new_state:
                self.gen.remove_post_file(cid)
                affected_users.add(info["owner_id"])

        # 2.5 [Critical] 预先更新所有变更文章的 URL 映射
        # 防止时序问题：如果 A 引用 B，且 B 变了。如果生成顺序是 A 先 B 后，
        # A 渲染时会查到 B 的旧 URL。必须先统一刷新所有任务的 URL 映射。
        if tasks:
            print(f"[Watcher] Pre-updating URL mappings for {len(tasks)} tasks...")
            for cid, info in tasks.items():
                username = self._get_username(info["owner_id"])
                data = info["data"]
                # 强制刷新数据库中的 URL 映射
                self.gen.url_mgr.register_mapping(
                    data["cid"], 
                    username, 
                    data.get("catagory", "default"), 
                    data.get("title", "untitled")
                )

        # 3. 执行更新生成 (此时所有文章的 URL 映射在数据库中已是最新)
        for cid, info in tasks.items():
            # 先删除旧文件(处理重命名情况)，remove_post_file 会清除 URLManager 内存映射
            # 但我们在 2.5 步已经刷新了 DB，renderer 会重新加载
            if cid in self._snapshot:
                # 注意：remove_post_file 内部调用 remove_mapping 会清除内存缓存
                # 但不影响我们刚刚写入 DB 的新映射
                self.gen.remove_post_file(cid)
            
            username = self._get_username(info["owner_id"])
            self.gen.sync_post_file(info["data"], username)
            affected_users.add(info["owner_id"])

        # 4. 更新索引
        for uid in affected_users:
            self.gen.sync_user_index(uid)

        self._snapshot = new_state

    def start(self, interval=3):
        self.gen.init_output_dir()
        self.running = True
        print(f"[*] DB Watcher started. Polling every {interval}s...")
        while self.running:
            try:
                self._scan()
            except Exception as e:
                print(f"[Watcher Error] {e}")
            time.sleep(interval)

    def stop(self):
        self.running = False