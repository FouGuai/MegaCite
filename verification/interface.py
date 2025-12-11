from abc import ABC, abstractmethod

class PlatformVerifier(ABC):
    @abstractmethod
    def login(self) -> bool:
        """交互式登录并保存 Cookie"""
        pass

    @abstractmethod
    def check_ownership(self, url: str) -> bool:
        """非交互式验证 URL 所有权"""
        pass