document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const guestArea = document.getElementById('auth-guest');
    const userArea = document.getElementById('auth-user');
    const usernameDisplay = document.getElementById('username-display');
    const btnLogout = document.getElementById('btn-logout');
    const linkMyHome = document.getElementById('link-my-home');
    
    // Auth Modal Elements
    const modalOverlay = document.getElementById('login-modal');
    const btnCancel = document.getElementById('btn-cancel-login');
    const btnSubmit = document.getElementById('btn-submit-auth');
    const inpUser = document.getElementById('inp-username');
    const inpPass = document.getElementById('inp-password');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');

    // QR Modal Elements
    const qrModal = document.getElementById('qr-modal');
    const qrImage = document.getElementById('qr-image');
    const qrLoading = document.getElementById('qr-loading');
    const btnCancelQr = document.getElementById('btn-cancel-qr');
    let authTimer = null;

    // Settings Page
    const settingsForm = document.getElementById('settings-form');
    const inpOldPass = document.getElementById('inp-old-pass');
    const inpNewPass = document.getElementById('inp-new-pass');
    let isRegisterMode = false;

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

    function updateUI() {
        const token = localStorage.getItem('mc_token');
        const username = localStorage.getItem('mc_username');
        if (token && username) {
            if(guestArea) guestArea.style.display = 'none';
            if(userArea) userArea.style.display = 'flex';
            if(usernameDisplay) usernameDisplay.textContent = username;
            if(linkMyHome) linkMyHome.href = `/${username}/index.html`;
        } else {
            if(guestArea) guestArea.style.display = 'inline-block';
            if(userArea) userArea.style.display = 'none';
        }
    }
    updateUI();

    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('mc_token');
            localStorage.removeItem('mc_username');
            updateUI();
            showToast('已退出登录');
            if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
                setTimeout(() => window.location.href = '/', 500);
            }
        });
    }

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
    loginTriggers.forEach(btn => btn.addEventListener('click', openModal));

    if (btnCancel) btnCancel.addEventListener('click', closeModal);
    if (modalOverlay) modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeModal(); });

    if (btnSubmit) {
        btnSubmit.addEventListener('click', async () => {
            const username = inpUser.value.trim();
            const password = inpPass.value.trim();
            if (!username || !password) { showToast('请填写完整信息'); return; }
            
            const originalText = btnSubmit.textContent;
            btnSubmit.disabled = true;
            btnSubmit.textContent = '处理中...';

            try {
                if (isRegisterMode) {
                    const regRes = await fetch('/api/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    if (!regRes.ok) throw new Error((await regRes.json()).error || '注册失败');
                }
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
                    showToast(isRegisterMode ? '注册成功' : '欢迎回来');
                    setTimeout(() => window.location.href = `/${username}/index.html`, 800);
                } else {
                    throw new Error((await loginRes.json()).error || '登录失败');
                }
            } catch (e) {
                showToast(e.message);
            } finally {
                btnSubmit.disabled = false;
                btnSubmit.textContent = originalText;
            }
        });
    }

    if (settingsForm) {
        if (!localStorage.getItem('mc_token')) window.location.href = '/';
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const res = await fetch('/api/change_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': localStorage.getItem('mc_token') },
                    body: JSON.stringify({ old_password: inpOldPass.value, new_password: inpNewPass.value })
                });
                if (res.ok) {
                    showToast('密码修改成功');
                    inpOldPass.value = ''; inpNewPass.value = '';
                } else {
                    showToast('失败: ' + (await res.json()).error);
                }
            } catch (e) {
                showToast('网络错误');
            }
        });
    }

    // --- QR / Screen Share Logic ---
    
    // 1. 点击图片区域发送坐标
    if (qrImage) {
        qrImage.addEventListener('click', async (e) => {
            const rect = qrImage.getBoundingClientRect();
            // 计算相对坐标
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            try {
                await fetch('/api/auth/interact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: 'click',
                        x: x,
                        y: y,
                        width: rect.width,
                        height: rect.height
                    })
                });
                // 添加点击反馈特效 (可选)
                const ripple = document.createElement('div');
                ripple.style.cssText = `position:fixed;left:${e.clientX}px;top:${e.clientY}px;width:10px;height:10px;background:rgba(255,0,0,0.5);border-radius:50%;pointer-events:none;transform:translate(-50%,-50%);animation:ripple 0.5s ease-out;`;
                document.body.appendChild(ripple);
                setTimeout(() => ripple.remove(), 500);
            } catch (err) {
                console.error("Interaction error:", err);
            }
        });
    }

    window.startAuth = async (platform) => {
        if (!qrModal) return;
        qrModal.classList.add('open');
        qrImage.style.display = 'none';
        qrLoading.style.display = 'block';
        qrLoading.textContent = '正在启动远程浏览器...';

        try {
            const initRes = await fetch('/api/auth/init', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ platform })
            });

            if (!initRes.ok) throw new Error('启动失败，请检查服务器日志 (Playwright是否安装?)');

            if (authTimer) clearInterval(authTimer);
            authTimer = setInterval(async () => {
                try {
                    const shotRes = await fetch('/api/auth/screenshot');
                    const shotData = await shotRes.json();
                    
                    if (shotData.image) {
                        qrImage.src = `data:image/png;base64,${shotData.image}`;
                        qrImage.style.display = 'block';
                        qrLoading.style.display = 'none';
                    }

                    const statusRes = await fetch('/api/auth/status');
                    const statusData = await statusRes.json();
                    if (statusData.status === 'success') {
                        clearInterval(authTimer);
                        showToast('绑定成功！');
                        qrModal.classList.remove('open');
                    }
                } catch (e) {
                    console.error("Polling error:", e);
                }
            }, 1000); 

        } catch (e) {
            showToast('错误: ' + e.message);
            qrModal.classList.remove('open');
        }
    };

    if (btnCancelQr) {
        btnCancelQr.addEventListener('click', async () => {
            if (authTimer) clearInterval(authTimer);
            qrModal.classList.remove('open');
            await fetch('/api/auth/cancel', { method: 'POST' });
        });
    }
});

// 添加 ripple 动画
const style = document.createElement('style');
style.innerHTML = `@keyframes ripple { 0% { width:0; height:0; opacity:1; } 100% { width:40px; height:40px; opacity:0; } }`;
document.head.appendChild(style);