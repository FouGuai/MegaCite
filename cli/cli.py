class Cli:
    """
    动态注册对外接口（Controller Layer）
    使用装饰器自动注册接口函数，无需手写 if-else 分支
    """

    def __init__(self):
        self.handlers = {}  # 存放接口名 → 函数映射

    # -------------------------
    # 装饰器：注册接口
    # -------------------------
    def api(self, name: str):
        """
        用法：
        @cli.api("create_post")
        def create_post(...): ...
        """
        def decorator(func):
            self.handlers[name] = func
            return func
        return decorator

    # -------------------------
    # 通用调用入口
    # -------------------------
    def call(self, name: str, **kwargs):
        """
        对外统一调用入口：
            cli.call("create_post", user_id=1, title="xx")
        """
        if name not in self.handlers:
            raise ValueError(f"API '{name}' not found")

        return self.handlers[name](**kwargs)
