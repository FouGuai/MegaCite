document.addEventListener('DOMContentLoaded', () => {
    // --- UI Elements ---
    const guestArea = document.getElementById('auth-guest');
    const userArea = document.getElementById('auth-user');
    const usernameDisplay = document.getElementById('username-display');
    const btnLogout = document.getElementById('btn-logout');
    const linkMyHome = document.getElementById('link-my-home');
    
    const modalOverlay = document.getElementById('login-modal');
    const btnCancel = document.getElementById('btn-cancel-login');
    const btnSubmit = document.getElementById('btn-submit-auth');
    const inpUser = document.getElementById('inp-username');
    const inpPass = document.getElementById('inp-password');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');

    const qrModal = document.getElementById('qr-modal');
    const qrImage = document.getElementById('qr-image');
    const qrLoading = document.getElementById('qr-loading');
    const btnCancelQr = document.getElementById('btn-cancel-qr');
    
    // State Variables
    let isAuthPolling = false;
    let currentSessionId = null;
    let isRegisterMode = false;

    const settingsForm = document.getElementById('settings-form');
    const inpOldPass = document.getElementById('inp-old-pass');
    const inpNewPass = document.getElementById('inp-new-pass');

    // --- Core Functions ---
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
            
            // 如果在设置页，加载绑定状态
            if (document.getElementById('platform-list')) {
                updateBindings();
            }
        } else {
            if(guestArea) guestArea.style.display = 'inline-block';
            if(userArea) userArea.style.display = 'none';
        }
    }

    // [新增] 获取绑定状态并更新按钮样式
    async function updateBindings() {
        try {
            const res = await fetch('/api/auth/bindings', {
                headers: { 'Authorization': localStorage.getItem('mc_token') }
            });
            const data = await res.json();
            const boundPlatforms = new Set(data.bindings || []);

            document.querySelectorAll('.btn-bind').forEach(btn => {
                const platform = btn.dataset.platform;
                btn.classList.remove('status-loading', 'status-bound', 'status-unbound');
                
                if (boundPlatforms.has(platform)) {
                    btn.textContent = '重新绑定';
                    btn.classList.add('status-bound');
                } else {
                    btn.textContent = '绑定';
                    btn.classList.add('status-unbound');
                }
                btn.disabled = false;
            });
        } catch (e) {
            console.error("Failed to fetch bindings", e);
        }
    }

    updateUI();

    // 坐标转换函数（保留以备将来使用）
    function convertCoordinates(clientX, clientY, imgElement) {
        const rect = imgElement.getBoundingClientRect();
        const displayX = clientX - rect.left;
        const displayY = clientY - rect.top;
        
        return {
            x: displayX,
            y: displayY,
            display_width: rect.width,
            display_height: rect.height
        };
    }

    // --- Auth Process Loop (轮询会话状态) ---
    async function pollLoop() {
        if (!isAuthPolling || !currentSessionId) return;

        try {
            const statusRes = await fetch(`/api/auth/status?session_id=${currentSessionId}`);
            const statusData = await statusRes.json();
            
            // 检查登录状态
            if (statusData.status === 'authenticated') {
                isAuthPolling = false;
                showToast('绑定成功！');
                qrModal.classList.remove('open');
                currentSessionId = null;
                updateBindings();
                return;
            } else if (statusData.status === 'failed') {
                isAuthPolling = false;
                showToast('绑定失败: ' + (statusData.error || '未知错误'));
                qrModal.classList.remove('open');
                currentSessionId = null;
                return;
            }
            // 'pending' 状态继续轮询
        } catch (e) {
            console.error('Poll error:', e);
        }

        if (isAuthPolling) {
            setTimeout(pollLoop, 500);
        }
    }

    window.startAuth = async (platform) => {
        try {
            const token = localStorage.getItem('mc_token');
            
            // 第1步：向服务器请求初始化验证会话
            const initRes = await fetch('/api/auth/init', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': token 
                },
                body: JSON.stringify({ platform })
            });
            
            if (!initRes.ok) {
                throw new Error('启动失败');
            }

            const initData = await initRes.json();
            currentSessionId = initData.session_id;
            
            showToast('正在启动验证客户端...');
            
            // 第2步：向本地客户端发送验证请求
            // 本地客户端应在 http://127.0.0.1:9999 监听
            const clientUrl = 'http://127.0.0.1:9999/verify';
            
            setTimeout(async () => {
                try {
                    const verifyRes = await fetch(clientUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            session_id: currentSessionId,
                            platform: platform,
                            server_url: window.location.origin
                        })
                    });
                    
                    if (verifyRes.ok) {
                        showToast('验证客户端已启动，请在浏览器中完成登录');
                        // 开始轮询检查验证状态
                        isAuthPolling = true;
                        pollLoop();
                    } else {
                        showToast('无法连接到本地客户端，请确保客户端正在运行');
                    }
                } catch (e) {
                    showToast('无法连接到本地客户端，请确保客户端正在运行\n' + 
                              '启动方式: python client/verifier.py --server ' + window.location.origin);
                }
            }, 500);

        } catch (e) {
            showToast('错误: ' + e.message);
        }
    };

    if (btnCancelQr) {
        btnCancelQr.addEventListener('click', async () => {
            isAuthPolling = false;
            qrModal.classList.remove('open');
            
            if (currentSessionId) {
                try {
                    await fetch('/api/auth/cancel', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_id: currentSessionId })
                    });
                } catch (e) {
                    console.error('Cancel error:', e);
                }
                currentSessionId = null;
            }
        });
    }

    // --- Standard Event Listeners ---
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            // 清除 LocalStorage 和 Cookie
            localStorage.removeItem('mc_token');
            localStorage.removeItem('mc_username');
            // 设置过期时间以删除 Cookie
            document.cookie = "mc_token=; path=/; max-age=0";
            
            updateUI();
            if (window.location.pathname.includes('settings')) window.location.href = '/';
        });
    }

    const openModal = () => { modalOverlay.classList.add('open'); inpUser.focus(); };
    const closeModal = () => { modalOverlay.classList.remove('open'); };
    
    document.querySelectorAll('#btn-login-trigger').forEach(b => b.addEventListener('click', openModal));
    if (btnCancel) btnCancel.addEventListener('click', closeModal);
    if (modalOverlay) modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeModal(); });

    if (btnSubmit) {
        btnSubmit.addEventListener('click', async () => {
            const u = inpUser.value.trim(), p = inpPass.value.trim();
            if (!u || !p) return showToast('请输入账号密码');
            
            try {
                if (isRegisterMode) {
                    await fetch('/api/register', { 
                        method: 'POST', 
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({username:u, password:p}) 
                    });
                }
                const res = await fetch('/api/login', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({username:u, password:p}) 
                });
                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('mc_token', data.token);
                    localStorage.setItem('mc_username', u);
                    document.cookie = `mc_token=${data.token}; path=/; max-age=86400`;
                    
                    closeModal();
                    updateUI();
                    showToast('登录成功');
                } else throw new Error('登录失败');
            } catch (e) { showToast(e.message); }
        });
    }

    if (tabLogin) {
        tabLogin.onclick = () => { isRegisterMode = false; tabLogin.classList.add('active'); tabRegister.classList.remove('active'); btnSubmit.textContent = '立即登录'; };
        tabRegister.onclick = () => { isRegisterMode = true; tabRegister.classList.add('active'); tabLogin.classList.remove('active'); btnSubmit.textContent = '注册并登录'; };
    }

    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const res = await fetch('/api/change_password', {
                    method: 'POST',
                    headers: { 
                        'Authorization': localStorage.getItem('mc_token'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        old_password: inpOldPass.value, 
                        new_password: inpNewPass.value 
                    })
                });
                if (res.ok) { 
                    showToast('密码修改成功'); 
                    inpOldPass.value=''; 
                    inpNewPass.value=''; 
                }
                else showToast('修改失败');
            } catch (e) { showToast('网络错误'); }
        });
    }
});