import time
from services.db import create_connection
from services.static_gen import StaticSiteGenerator

class DBWatcher:
    """
    后台轮询监听器。
    周期性检查数据库指纹，发现变化时调用 Generator。
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
                    sig = hash(tuple(data_map.values()))
                    state[cid] = {"owner_id": owner_id, "data": data_map, "signature": sig}
        finally:
            conn.close()
        return state

    def _trigger_update(self, info):
        conn = create_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users WHERE id=%s", (info["owner_id"],))
                row = cur.fetchone()
                if row:
                    self.gen.sync_post_file(info["data"], row[0])
        finally:
            conn.close()

    def _scan(self):
        new_state = self._get_current_state()
        affected_users = set()

        # 1. 变更检测
        for cid, info in new_state.items():
            old_info = self._snapshot.get(cid)
            if not old_info or old_info["signature"] != info["signature"]:
                if old_info:
                     self.gen.remove_post_file(cid) # 清理旧文件
                self._trigger_update(info)
                affected_users.add(info["owner_id"])

        # 2. 删除检测
        for cid, info in self._snapshot.items():
            if cid not in new_state:
                self.gen.remove_post_file(cid)
                affected_users.add(info["owner_id"])

        # 3. 更新索引
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