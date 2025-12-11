document.addEventListener('DOMContentLoaded', () => {
    // Materialize 初始化
    M.Modal.init(document.querySelectorAll('.modal'));
    M.Tooltip.init(document.querySelectorAll('.tooltipped'));

    // Auth 元素
    const guestArea = document.getElementById('auth-guest');
    const userArea = document.getElementById('auth-user');
    const btnLogout = document.getElementById('btn-logout');
    
    // Login Modal 元素
    const modalElem = document.getElementById('login-modal');
    const modalInstance = M.Modal.getInstance(modalElem);
    const btnSubmit = document.getElementById('btn-submit-login');
    const inpUser = document.getElementById('inp-username');
    const inpPass = document.getElementById('inp-password');

    function updateUI() {
        const token = localStorage.getItem('mc_token');
        // 使用 CSS 类 'hide' (Materialize 内置) 来控制显示
        if (token) {
            guestArea.classList.add('hide');
            userArea.classList.remove('hide');
        } else {
            guestArea.classList.remove('hide');
            userArea.classList.add('hide');
        }
    }

    updateUI();

    // 登出
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('mc_token');
            updateUI();
            M.toast({html: '已安全退出', classes: 'rounded'});
        });
    }

    // 登录
    if (btnSubmit) {
        btnSubmit.addEventListener('click', async () => {
            const username = inpUser.value;
            const password = inpPass.value;

            if (!username || !password) {
                M.toast({html: '请输入完整信息', classes: 'rounded red'});
                return;
            }
            
            const originalText = btnSubmit.innerHTML;
            btnSubmit.classList.add('disabled');
            btnSubmit.innerHTML = '验证中...';

            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('mc_token', data.token);
                    
                    inpUser.value = '';
                    inpPass.value = '';
                    modalInstance.close();
                    updateUI();
                    M.toast({html: '欢迎回来', classes: 'rounded green'});
                } else {
                    const err = await res.json();
                    M.toast({html: '验证失败: ' + (err.error || '未知错误'), classes: 'rounded red'});
                }
            } catch (e) {
                M.toast({html: '无法连接到服务器', classes: 'rounded red'});
            } finally {
                btnSubmit.classList.remove('disabled');
                btnSubmit.innerHTML = originalText;
            }
        });
    }
});