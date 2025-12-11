document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const guestArea = document.getElementById('auth-guest');
    const userArea = document.getElementById('auth-user');
    const usernameDisplay = document.getElementById('username-display');
    const btnLogout = document.getElementById('btn-logout');
    const linkMyHome = document.getElementById('link-my-home');
    
    // Modal Elements
    const modalOverlay = document.getElementById('login-modal');
    const btnCancel = document.getElementById('btn-cancel-login');
    const btnSubmit = document.getElementById('btn-submit-auth');
    const inpUser = document.getElementById('inp-username');
    const inpPass = document.getElementById('inp-password');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');

    // Settings Page Elements
    const settingsForm = document.getElementById('settings-form');
    const inpOldPass = document.getElementById('inp-old-pass');
    const inpNewPass = document.getElementById('inp-new-pass');

    let isRegisterMode = false;

    // --- Toast Function ---
    function showToast(message) {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    // --- Auth State ---
    function updateUI() {
        const token = localStorage.getItem('mc_token');
        const username = localStorage.getItem('mc_username');
        
        if (token && username) {
            if(guestArea) guestArea.style.display = 'none';
            if(userArea) userArea.style.display = 'flex';
            if(usernameDisplay) {
                usernameDisplay.textContent = username;
            }
            if(linkMyHome) {
                linkMyHome.href = `/${username}/index.html`;
            }
        } else {
            if(guestArea) guestArea.style.display = 'inline-block';
            if(userArea) userArea.style.display = 'none';
        }
    }
    updateUI();

    // --- Event Listeners ---

    // Logout
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('mc_token');
            localStorage.removeItem('mc_username');
            updateUI();
            showToast('已退出登录');
            // 如果在设置页，退回首页
            if (window.location.pathname.includes('settings.html')) {
                window.location.href = '/';
            }
        });
    }

    // Modal Control
    const openModal = (e) => {
        if(e) e.preventDefault();
        if(modalOverlay) modalOverlay.classList.add('open');
    };
    const closeModal = () => {
        if(modalOverlay) modalOverlay.classList.remove('open');
        if(inpUser) inpUser.value = '';
        if(inpPass) inpPass.value = '';
    };

    const switchTab = (toRegister) => {
        isRegisterMode = toRegister;
        if (toRegister) {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            if(btnSubmit) btnSubmit.textContent = '注册';
        } else {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            if(btnSubmit) btnSubmit.textContent = '登录';
        }
    };

    if (tabLogin) tabLogin.onclick = () => switchTab(false);
    if (tabRegister) tabRegister.onclick = () => switchTab(true);

    const loginTriggers = document.querySelectorAll('#btn-login-trigger');
    loginTriggers.forEach(btn => {
        btn.addEventListener('click', openModal);
    });

    if (btnCancel) btnCancel.addEventListener('click', closeModal);
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closeModal();
        });
    }

    // Auth Action (Login / Register)
    if (btnSubmit) {
        btnSubmit.addEventListener('click', async () => {
            const username = inpUser.value;
            const password = inpPass.value;

            if (!username || !password) {
                showToast('请输入完整信息');
                return;
            }
            
            const originalText = btnSubmit.textContent;
            btnSubmit.disabled = true;
            btnSubmit.textContent = '处理中...';

            const endpoint = isRegisterMode ? '/api/register' : '/api/login';

            try {
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                if (res.ok) {
                    const data = await res.json();
                    
                    if (isRegisterMode) {
                        showToast('注册成功，请登录');
                        switchTab(false); // 切换回登录页
                    } else {
                        localStorage.setItem('mc_token', data.token);
                        localStorage.setItem('mc_username', username); // 保存用户名
                        
                        closeModal();
                        updateUI();
                        showToast('登录成功');

                        // Admin 跳转逻辑
                        if (username === 'admin') {
                            setTimeout(() => {
                                window.location.href = '/admin/index.html';
                            }, 500);
                        } else {
                            // 普通用户跳转到自己的主页
                            setTimeout(() => {
                                window.location.href = `/${username}/index.html`;
                            }, 500);
                        }
                    }
                } else {
                    const err = await res.json();
                    showToast('操作失败: ' + (err.error || '未知错误'));
                }
            } catch (e) {
                showToast('无法连接到服务器');
            } finally {
                btnSubmit.disabled = false;
                btnSubmit.textContent = originalText;
            }
        });
    }

    // Settings Page Logic
    if (settingsForm) {
        // 检查是否登录
        if (!localStorage.getItem('mc_token')) {
            window.location.href = '/';
        }

        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const oldPass = inpOldPass.value;
            const newPass = inpNewPass.value;

            if (!oldPass || !newPass) {
                showToast('请填写所有字段');
                return;
            }

            try {
                const res = await fetch('/api/change_password', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': localStorage.getItem('mc_token') 
                    },
                    body: JSON.stringify({ old_password: oldPass, new_password: newPass })
                });

                if (res.ok) {
                    showToast('密码修改成功');
                    inpOldPass.value = '';
                    inpNewPass.value = '';
                } else {
                    const err = await res.json();
                    showToast('失败: ' + (err.error || '未知错误'));
                }
            } catch (e) {
                showToast('网络错误');
            }
        });
    }
});