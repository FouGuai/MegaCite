from abc import ABC, abstractmethod

class PlatformVerifier(ABC):
    @abstractmethod
    def login(self) -> bool:
        """[Legacy] 交互式同步登录"""
        pass

    @abstractmethod
    def check_ownership(self, url: str) -> bool:
        """非交互式验证 URL 所有权"""
        pass

    # --- 异步会话与交互接口 ---

    def start_login_session(self) -> None:
        """启动无头浏览器会话"""
        raise NotImplementedError("Not supported.")

    def get_login_screenshot(self) -> str | None:
        """获取当前登录页面的 Base64 截图"""
        return None

    def handle_interaction(self, action: str, payload: dict) -> None:
        """处理前端传来的交互操作 (如点击)"""
        pass

    def check_login_status(self) -> bool:
        """检查当前会话是否登录成功"""
        return False

    def close_session(self) -> None:
        """关闭会话资源"""
        pass