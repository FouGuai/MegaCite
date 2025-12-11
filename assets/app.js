document.addEventListener('DOMContentLoaded', () => {
    // --- UI Elements ---
    const guestArea = document.getElementById('auth-guest');
    const userArea = document.getElementById('auth-user');
    const usernameDisplay = document.getElementById('username-display');
    const btnLogout = document.getElementById('btn-logout');
    const linkMyHome = document.getElementById('link-my-home');
    
    // Modals
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
    let lastMouseMove = 0; 
    let isRegisterMode = false;

    // Settings Form
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
                // 移除不可点击状态
                btn.disabled = false;
            });
        } catch (e) {
            console.error("Failed to fetch bindings", e);
        }
    }

    updateUI();

    // --- Interaction Logic (点击 & 鼠标移动) ---
    async function sendInteraction(type, data) {
        if (!isAuthPolling) return;
        try {
            await fetch('/api/auth/interact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, ...data })
            });
        } catch (e) { console.error(e); }
    }

    if (qrImage) {
        // 点击交互
        qrImage.addEventListener('click', (e) => {
            const rect = qrImage.getBoundingClientRect();
            sendInteraction('click', {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top,
                width: rect.width,
                height: rect.height
            });
        });

        // 鼠标移动交互 (模拟 Hover 效果，节流处理)
        qrImage.addEventListener('mousemove', (e) => {
            const now = Date.now();
            if (now - lastMouseMove > 80) { // 约 12fps 的采样率
                lastMouseMove = now;
                const rect = qrImage.getBoundingClientRect();
                sendInteraction('mousemove', {
                    x: e.clientX - rect.left,
                    y: e.clientY - rect.top,
                    width: rect.width,
                    height: rect.height
                });
            }
        });
    }

    // --- Auth Process Loop (Stream) ---
    async function pollLoop() {
        if (!isAuthPolling) return;

        try {
            // 并行请求：同时获取截图和状态
            const [shotRes, statusRes] = await Promise.all([
                fetch('/api/auth/screenshot'),
                fetch('/api/auth/status')
            ]);

            const shotData = await shotRes.json();
            const statusData = await statusRes.json();
            
            if (shotData.image) {
                qrImage.src = `data:image/png;base64,${shotData.image}`;
                qrImage.style.display = 'block';
                qrLoading.style.display = 'none';
            }

            if (statusData.status === 'success') {
                isAuthPolling = false;
                showToast('绑定成功！');
                qrModal.classList.remove('open');
                updateBindings(); // 成功后刷新按钮状态
                return;
            }
        } catch (e) {
            // 忽略网络错误，继续尝试
        }

        if (isAuthPolling) {
            // 使用 setTimeout 而非 setInterval，防止网络卡顿时请求堆积
            setTimeout(pollLoop, 150); 
        }
    }

    window.startAuth = async (platform) => {
        if (!qrModal) return;
        qrModal.classList.add('open');
        qrImage.style.display = 'none';
        qrLoading.style.display = 'block';
        qrLoading.textContent = '正在连接远程浏览器...';

        try {
            const initRes = await fetch('/api/auth/init', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ platform })
            });
            
            if (!initRes.ok) {
                throw new Error('启动失败，请检查服务器日志');
            }

            isAuthPolling = true;
            pollLoop(); 

        } catch (e) {
            showToast('错误: ' + e.message);
            qrModal.classList.remove('open');
        }
    };

    if (btnCancelQr) {
        btnCancelQr.addEventListener('click', async () => {
            isAuthPolling = false;
            qrModal.classList.remove('open');
            await fetch('/api/auth/cancel', { method: 'POST' });
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
                if (isRegisterMode) await fetch('/api/register', { method: 'POST', body: JSON.stringify({username:u, password:p}) });
                const res = await fetch('/api/login', { method: 'POST', body: JSON.stringify({username:u, password:p}) });
                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('mc_token', data.token);
                    localStorage.setItem('mc_username', u);
                    // [关键] 写入 Cookie 以便后端拦截静态页面请求
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
                    headers: { 'Authorization': localStorage.getItem('mc_token') },
                    body: JSON.stringify({ old_password: inpOldPass.value, new_password: inpNewPass.value })
                });
                if (res.ok) { showToast('密码修改成功'); inpOldPass.value=''; inpNewPass.value=''; }
                else showToast('修改失败');
            } catch (e) { showToast('网络错误'); }
        });
    }
});