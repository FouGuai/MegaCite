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

    // --- Toast Function (Updated for better visuals) ---
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
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
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
            // 如果在设置页或私人主页，退回 Landing Page
            if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
                setTimeout(() => window.location.href = '/', 500);
            }
        });
    }

    // Modal Control
    const openModal = (e) => {
        if(e) e.preventDefault();
        if(modalOverlay) modalOverlay.classList.add('open');
        if(inpUser) inpUser.focus();
    };
    const closeModal = () => {
        if(modalOverlay) modalOverlay.classList.remove('open');
        setTimeout(() => {
            if(inpUser) inpUser.value = '';
            if(inpPass) inpPass.value = '';
        }, 200);
    };

    const switchTab = (toRegister) => {
        isRegisterMode = toRegister;
        if (toRegister) {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            if(btnSubmit) btnSubmit.textContent = '注册并登录';
        } else {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            if(btnSubmit) btnSubmit.textContent = '立即登录';
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
            const username = inpUser.value.trim();
            const password = inpPass.value.trim();

            if (!username || !password) {
                showToast('请填写完整信息');
                return;
            }
            
            const originalText = btnSubmit.textContent;
            btnSubmit.disabled = true;
            btnSubmit.textContent = '处理中...';

            const endpoint = isRegisterMode ? '/api/register' : '/api/login';

            try {
                // 如果是注册，先注册再自动尝试登录
                if (isRegisterMode) {
                    const regRes = await fetch('/api/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    if (!regRes.ok) {
                        const err = await regRes.json();
                        throw new Error(err.error || '注册失败');
                    }
                }

                // 统一执行登录
                const loginRes = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                if (loginRes.ok) {
                    const data = await loginRes.json();
                    localStorage.setItem('mc_token', data.token);
                    localStorage.setItem('mc_username', username);
                    
                    closeModal();
                    updateUI();
                    showToast(isRegisterMode ? '注册成功，已自动登录' : '欢迎回来');

                    setTimeout(() => {
                        window.location.href = `/${username}/index.html`;
                    }, 800);
                } else {
                    const err = await loginRes.json();
                    throw new Error(err.error || '登录失败');
                }
            } catch (e) {
                showToast(e.message || '网络连接错误');
            } finally {
                btnSubmit.disabled = false;
                btnSubmit.textContent = originalText;
            }
        });
    }

    // Settings Page Logic
    if (settingsForm) {
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

            const btn = settingsForm.querySelector('button');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = '修改中...';

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
                    showToast('操作失败: ' + (err.error || '未知错误'));
                }
            } catch (e) {
                showToast('网络错误');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        });
    }
});