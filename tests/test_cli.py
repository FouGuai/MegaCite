import sys
import pytest
from unittest.mock import patch, ANY
import cli

@pytest.fixture
def run_cli(capsys):
    def _run(args, inputs=None):
        input_list = inputs or []
        input_iter = iter(input_list)
        with patch.object(sys, "argv", ["cli.py"] + args):
            with patch("builtins.input", side_effect=input_iter), \
                 patch("getpass.getpass", side_effect=input_iter):
                try:
                    cli.main()
                except SystemExit: pass 
                except StopIteration: pass 
        return capsys.readouterr()
    return _run

@patch("client.store.load_local_token", return_value="mock_token")
class TestPostCommands:
    @patch("services.post_service.post_create")
    def test_create_success(self, mock_create, mock_load, run_cli):
        """[P-02] 创建成功 (自动 CID)"""
        # 模拟 service 返回一个生成的 CID
        mock_create.return_value = "auto_gen_cid_123"
        
        # 命令行不再需要 CID 参数
        out = run_cli(["post", "create"])
        
        # 验证调用时不再传参
        mock_create.assert_called_with("mock_token")
        assert "Post created. CID: auto_gen_cid_123" in out.out

    @patch("services.post_service.post_list")
    def test_list(self, mock_list, mock_load, run_cli):
        mock_list.return_value = ["cid1"]
        out = run_cli(["post", "list"])
        assert "Posts: ['cid1']" in out.out