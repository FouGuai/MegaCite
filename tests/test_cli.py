import sys
import pytest
from unittest.mock import patch, ANY
import cli

# ==========================================
# 🔧 测试工具 (Fixtures)
# ==========================================

@pytest.fixture
def run_cli(capsys):
    """
    运行 CLI 命令并捕获输出的辅助函数。
    模拟 sys.argv, input 和 getpass。
    """
    def _run(args, inputs=None):
        input_list = inputs or []
        input_iter = iter(input_list)
        
        with patch.object(sys, "argv", ["cli.py"] + args):
            with patch("builtins.input", side_effect=input_iter), \
                 patch("getpass.getpass", side_effect=input_iter):
                try:
                    cli.main()
                except SystemExit:
                    pass 
                except StopIteration:
                    pass 
        return capsys.readouterr()
    return _run

# ==========================================
# 🧪 1. 服务端测试 (Server Command)
# ==========================================

@patch("services.server_service.server_start")
def test_server_start_success(mock_start, run_cli):
    """[S-01] Server Start 成功"""
    run_cli(["server", "start", "8080"])
    mock_start.assert_called_once_with(8080)

@patch("services.server_service.server_start")
def test_server_start_failure(mock_start, run_cli):
    """[S-02] Server Start 失败"""
    mock_start.side_effect = Exception("Permission denied")
    
    out = run_cli(["server", "start", "80"])
    
    assert "Error: Permission denied" in out.out.strip()

# ==========================================
# 🧪 2. 用户管理测试 (User Commands)
# ==========================================

@patch("services.auth_service.user_register")
def test_user_register_success(mock_reg, run_cli):
    """[U-01] 注册成功"""
    mock_reg.return_value = 101
    
    out = run_cli(["user", "register"], inputs=["alice", "pw"])
    
    assert "User registered successfully. ID: 101" == out.out.strip()

@patch("services.auth_service.user_register")
def test_user_register_failure(mock_reg, run_cli):
    """[U-02] 注册失败 (重复用户)"""
    mock_reg.side_effect = Exception("Username taken")
    
    out = run_cli(["user", "register"], inputs=["alice", "pw"])
    
    assert "Error: Username taken" == out.out.strip()

@patch("client.store.save_local_token")
@patch("services.auth_service.user_login")
def test_user_login_success(mock_login, mock_save, run_cli):
    """[U-03] 登录成功"""
    mock_login.return_value = "tok_123"
    
    out = run_cli(["user", "login"], inputs=["alice", "pw"])
    
    mock_save.assert_called_once_with("tok_123")
    assert "Login successful. Token saved locally." == out.out.strip()

@patch("services.auth_service.user_login")
def test_user_login_failure(mock_login, run_cli):
    """[U-04] 登录失败 (密码错误)"""
    mock_login.side_effect = ValueError("Invalid password")
    
    out = run_cli(["user", "login"], inputs=["alice", "wrong"])
    
    assert "Error: Invalid password" == out.out.strip()

@patch("client.store.clear_local_token")
def test_user_logout(mock_clear, run_cli):
    """[U-05] 登出"""
    out = run_cli(["user", "logout"])
    
    mock_clear.assert_called_once()
    assert "Logged out." == out.out.strip()

# ==========================================
# 🧪 3. 权限拦截测试 (Permission Guard)
# ==========================================

def test_permission_denied(run_cli):
    """[P-00] 未登录状态下操作 Post (Service 抛出 PermissionError)"""
    with patch("client.store.load_local_token", return_value=None):
        # 模拟 Service 层检测到 token 无效/空时抛出异常
        with patch("services.post_service.post_list", side_effect=PermissionError("No token")):
            out = run_cli(["post", "list"])
            
            # 严格匹配异常处理块中的输出
            expected = "Error: Permission denied. Please login first using 'python cli.py user login'."
            assert expected == out.out.strip()

# ==========================================
# 🧪 4. 文章管理测试 (Post Commands)
# ==========================================

# 默认模拟已登录状态 (返回 mock_token)
@patch("client.store.load_local_token", return_value="mock_token")
class TestPostCommands:

    @patch("services.post_service.post_list")
    def test_list(self, mock_list, mock_load, run_cli):
        """[P-01] 列表显示"""
        mock_list.return_value = ["cid1", "cid2"]
        
        out = run_cli(["post", "list"])
        
        mock_list.assert_called_with("mock_token", None)
        assert "Posts: ['cid1', 'cid2']" == out.out.strip()

    @patch("services.post_service.post_create")
    def test_create_success(self, mock_create, mock_load, run_cli):
        """[P-02] 创建成功"""
        out = run_cli(["post", "create", "new_cid"])
        
        mock_create.assert_called_with("mock_token", "new_cid")
        assert "Post new_cid created." == out.out.strip()

    @patch("services.post_service.post_create")
    def test_create_failure(self, mock_create, mock_load, run_cli):
        """[P-03] 创建失败 (CID 重复)"""
        mock_create.side_effect = Exception("Duplicate CID")
        
        out = run_cli(["post", "create", "dup_cid"])
        
        assert "Error: Duplicate CID" == out.out.strip()

    @patch("services.post_service.post_update")
    def test_update_success(self, mock_update, mock_load, run_cli):
        """[P-04] 更新成功"""
        mock_update.return_value = True
        
        out = run_cli(["post", "update", "cid1", "title", "New Title"])
        
        mock_update.assert_called_with("mock_token", "cid1", "title", "New Title")
        assert "Update success" == out.out.strip()

    @patch("services.post_service.post_update")
    def test_update_failure(self, mock_update, mock_load, run_cli):
        """[P-05] 更新失败 (目标不存在)"""
        mock_update.return_value = False
        
        out = run_cli(["post", "update", "cid9", "title", "New Title"])
        
        assert "Update failed" == out.out.strip()

    @patch("services.post_service.post_delete")
    def test_delete_success(self, mock_delete, mock_load, run_cli):
        """[P-06] 删除成功"""
        mock_delete.return_value = True
        
        out = run_cli(["post", "delete", "cid1"])
        
        assert "Delete success" == out.out.strip()

    @patch("services.post_service.post_delete")
    def test_delete_failure(self, mock_delete, mock_load, run_cli):
        """[P-07] 删除失败 (目标不存在)"""
        mock_delete.return_value = False
        
        out = run_cli(["post", "delete", "cid9"])
        
        assert "Delete failed" == out.out.strip()

    @patch("services.post_service.post_get")
    def test_get_success(self, mock_get, mock_load, run_cli):
        """[P-08] 获取字段成功"""
        mock_get.return_value = "Some Content"
        
        out = run_cli(["post", "get", "cid1", "context"])
        
        assert "context: Some Content" == out.out.strip()

    @patch("services.post_service.post_get")
    def test_get_failure(self, mock_get, mock_load, run_cli):
        """[P-09] 获取字段失败 (返回 None)"""
        mock_get.return_value = None
        
        out = run_cli(["post", "get", "cid1", "date"])
        
        assert "date: None" == out.out.strip()

    @patch("services.post_service.post_search")
    def test_search(self, mock_search, mock_load, run_cli):
        """[P-10] 搜索结果"""
        mock_search.return_value = ["cid1"]
        
        out = run_cli(["post", "search", "keyword"])
        
        mock_search.assert_called_with("mock_token", "keyword")
        assert "Search results: ['cid1']" == out.out.strip()