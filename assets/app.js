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
    const btnCancelQr = document.getElementById('btn-cancel-qr');

    const settingsForm = document.getElementById('settings-form');
    const inpOldPass = document.getElementById('inp-old-pass');
    const inpNewPass = document.getElementById('inp-new-pass');

    // Dashboard Elements
    const dashboardActions = document.getElementById('dashboard-actions');
    const btnCreatePost = document.getElementById('btn-create-post');
    const btnMigrateTrigger = document.getElementById('btn-migrate-trigger');
    
    // Migrate Modal Elements
    const migrateModal = document.getElementById('migrate-modal');
    const inpMigrateUrl = document.getElementById('inp-migrate-url');
    const btnStartMigrate = document.getElementById('btn-start-migrate');
    const btnCancelMigrate = document.getElementById('btn-cancel-migrate');
    const btnStopMigrate = document.getElementById('btn-stop-migrate'); 
    const migrateInputArea = document.getElementById('migrate-input-area');
    const migrateProgressArea = document.getElementById('migrate-progress-area');
    const migrateLogs = document.getElementById('migrate-logs');
    const btnCloseMigrate = document.getElementById('btn-close-migrate');
    
    // Delete Modal Elements
    const deleteModal = document.getElementById('delete-modal');
    const btnConfirmDelete = document.getElementById('btn-confirm-delete');
    const btnCancelDelete = document.getElementById('btn-cancel-delete');
    let deleteTargetCid = null;

    // Editor Elements
    const editTitle = document.getElementById('edit-title');
    const editDescription = document.getElementById('edit-description'); // [新增]
    const editCategorySelect = document.getElementById('edit-category-select');
    const editCategoryInput = document.getElementById('edit-category-input');
    const editPreview = document.getElementById('edit-preview');
    const btnSavePost = document.getElementById('btn-save');
    const btnBack = document.getElementById('btn-back');
    const btnEditTrigger = document.getElementById('btn-edit-trigger');
    const monacoContainer = document.getElementById('monaco-container');

    // State Variables
    let currentSessionId = null;
    let authEventSource = null; 
    let isRegisterMode = false;
    let migrateAbortController = null; 
    let editorInstance = null; // Monaco Instance
    let isEditorDirty = false; // 未保存标记

    // Icons for Password Toggle
    const iconEye = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
    const iconEyeOff = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';

    // --- Password Toggle Logic ---
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.previousElementSibling;
            if (!input) return;
            
            if (input.type === 'password') {
                input.type = 'text';
                toggle.innerHTML = iconEye;
            } else {
                input.type = 'password';
                toggle.innerHTML = iconEyeOff;
            }
        });
    });

    if (inpPass) {
        inpPass.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                btnSubmit.click();
            }
        });
    }

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

    const pendingToast = localStorage.getItem('mc_pending_toast');
    if (pendingToast) {
        showToast(pendingToast);
        localStorage.removeItem('mc_pending_toast');
    }

    function updateUI() {
        const token = localStorage.getItem('mc_token');
        const username = localStorage.getItem('mc_username');
        if (token && username) {
            if(guestArea) guestArea.style.display = 'none';
            if(userArea) userArea.style.display = 'flex';
            if(usernameDisplay) usernameDisplay.textContent = username;
            if(linkMyHome) linkMyHome.href = `/${username}/index.html`;
            
            // 1. 首页控制台逻辑
            const pageOwnerMeta = document.querySelector('meta[name="page-owner"]');
            if (pageOwnerMeta && dashboardActions) {
                const pageOwner = pageOwnerMeta.getAttribute('content');
                if (pageOwner === username) {
                    dashboardActions.style.display = 'flex';
                    document.querySelectorAll('.btn-delete-post').forEach(btn => {
                        btn.style.display = 'block';
                    });
                }
            }

            // 2. 文章页编辑按钮逻辑
            const postAuthorMeta = document.querySelector('meta[name="post-author"]');
            if (postAuthorMeta && btnEditTrigger) {
                const postAuthor = postAuthorMeta.getAttribute('content');
                if (postAuthor === username) {
                    btnEditTrigger.style.display = 'inline-flex';
                    const cid = document.querySelector('meta[name="post-cid"]').getAttribute('content');
                    
                    btnEditTrigger.onclick = () => {
                        window.location.href = `/edit.html?cid=${cid}`;
                    };
                }
            }

            if (document.getElementById('platform-list')) {
                updateBindings();
            }
        } else {
            if(guestArea) guestArea.style.display = 'inline-block';
            if(userArea) userArea.style.display = 'none';
            if(dashboardActions) dashboardActions.style.display = 'none';
        }
    }

    async function updateBindings() {
        try {
            const res = await fetch('/api/auth/bindings', {
                headers: { 'Authorization': localStorage.getItem('mc_token') }
            });
            const data = await res.json();
            const boundPlatforms = new Set(data.bindings || []);

            document.querySelectorAll('.btn-bind').forEach(btn => {
                const platform = btn.dataset.platform;
                if (!platform) return;
                btn.classList.remove('status-loading', 'status-bound', 'status-unbound');
                
                if (boundPlatforms.has(platform)) {
                    btn.textContent = '更新'; 
                    btn.classList.add('status-bound'); 
                } else {
                    btn.textContent = '绑定'; 
                    btn.classList.add('status-unbound'); 
                }
                btn.disabled = false;
            });

            document.querySelectorAll('.btn-unbind').forEach(btn => {
                const platform = btn.dataset.platform;
                if (boundPlatforms.has(platform)) {
                    btn.style.display = 'inline-block';
                } else {
                    btn.style.display = 'none';
                }
            });

        } catch (e) {
            console.error("Failed to fetch bindings", e);
        }
    }

    window.unbindAuth = async (platform) => {
        if (!confirm(`确定要解除 ${platform} 的绑定吗？这意味着您将无法自动同步该平台的文章。`)) return;

        try {
            const res = await fetch('/api/auth/unbind', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': localStorage.getItem('mc_token')
                },
                body: JSON.stringify({ platform })
            });
            
            if (res.ok) {
                showToast('已解除绑定');
                updateBindings();
            } else {
                showToast('解绑失败');
            }
        } catch (e) {
            showToast('网络错误');
        }
    };

    updateUI();

    // --- Editor Logic (Monaco + Sync) ---
    if (monacoContainer) {
        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }});

        const params = new URLSearchParams(window.location.search);
        const cid = params.get('cid');
        
        if (!cid) {
            showToast('参数错误: 缺少 CID');
            return;
        }

        const markDirty = () => {
            if (!isEditorDirty) {
                isEditorDirty = true;
                document.title = "编辑器 * - MegaCite";
            }
        };

        const markClean = () => {
            isEditorDirty = false;
            document.title = "编辑器 - MegaCite";
        };

        // 监听基础输入框变化
        editTitle.addEventListener('input', markDirty);
        if (editDescription) editDescription.addEventListener('input', markDirty);
        editCategorySelect.addEventListener('change', markDirty);
        editCategoryInput.addEventListener('input', markDirty);

        // 拦截退出行为
        window.addEventListener('beforeunload', (e) => {
            if (isEditorDirty) {
                e.preventDefault();
                e.returnValue = ''; 
            }
        });

        // Initialize Monaco and Data
        require(['vs/editor/editor.main'], async () => {
            try {
                // 1. 获取文章详情
                const postRes = await fetch(`/api/post/detail?cid=${cid}`, {
                    headers: { 'Authorization': localStorage.getItem('mc_token') }
                });
                if (!postRes.ok) throw new Error("加载文章失败");
                const postData = await postRes.json();

                // 2. 获取分类列表
                const catRes = await fetch('/api/categories');
                const catData = await catRes.json();
                
                // 填充 Select
                const categories = catData.categories || [];
                const validCats = categories.filter(c => c !== 'Default' && c !== '__NEW__');
                
                editCategorySelect.innerHTML = `<option value="Default">Default</option>`;
                validCats.forEach(cat => {
                    const opt = document.createElement('option');
                    opt.value = cat;
                    opt.textContent = cat;
                    editCategorySelect.appendChild(opt);
                });
                editCategorySelect.innerHTML += `<option value="__NEW__" style="font-weight:bold;color:var(--vp-c-brand)">+ 新建分类...</option>`;

                // 设置初始值
                editTitle.value = postData.title || '';
                if (editDescription) editDescription.value = postData.description || '';
                
                if (validCats.includes(postData.category)) {
                    editCategorySelect.value = postData.category;
                } else if (postData.category !== 'Default') {
                    const opt = document.createElement('option');
                    opt.value = postData.category;
                    opt.textContent = postData.category;
                    editCategorySelect.insertBefore(opt, editCategorySelect.lastElementChild);
                    editCategorySelect.value = postData.category;
                } else {
                    editCategorySelect.value = 'Default';
                }

                // 3. 创建 Monaco 实例
                editorInstance = monaco.editor.create(monacoContainer, {
                    value: postData.context || '',
                    language: 'markdown',
                    theme: 'vs', 
                    automaticLayout: true,
                    wordWrap: 'on',
                    minimap: { enabled: false },
                    fontSize: 14,
                    padding: { top: 20, bottom: 20 },
                    scrollBeyondLastLine: false,
                    // [修改] 确保使用等宽字体
                    fontFamily: "'Roboto Mono', 'Menlo', 'Monaco', 'Courier New', monospace"
                });

                // 4. 初始预览渲染
                if (window.marked) {
                    editPreview.innerHTML = marked.parse(postData.context || '');
                }

                // 5. 实时预览 + 滚动同步事件
                editorInstance.onDidChangeModelContent(() => {
                    markDirty(); // 标记变动
                    const newVal = editorInstance.getValue();
                    if (window.marked) {
                        editPreview.innerHTML = marked.parse(newVal);
                    }
                });

                // [滚动同步逻辑] 使用 Lodash throttle 节流
                const syncPreviewScroll = _.throttle(() => {
                    const editorScrollTop = editorInstance.getScrollTop();
                    const editorScrollHeight = editorInstance.getScrollHeight();
                    const editorViewportHeight = editorInstance.getLayoutInfo().height;
                    
                    const scrollPercentage = editorScrollTop / (editorScrollHeight - editorViewportHeight);
                    
                    const previewScrollHeight = editPreview.scrollHeight;
                    const previewViewportHeight = editPreview.clientHeight;
                    
                    editPreview.scrollTop = scrollPercentage * (previewScrollHeight - previewViewportHeight);
                }, 20); 

                const syncEditorScroll = _.throttle(() => {
                    const previewScrollTop = editPreview.scrollTop;
                    const previewScrollHeight = editPreview.scrollHeight;
                    const previewViewportHeight = editPreview.clientHeight;
                    
                    const scrollPercentage = previewScrollTop / (previewScrollHeight - previewViewportHeight);
                    
                    const editorScrollHeight = editorInstance.getScrollHeight();
                    const editorViewportHeight = editorInstance.getLayoutInfo().height;
                    
                    editorInstance.setScrollTop(scrollPercentage * (editorScrollHeight - editorViewportHeight));
                }, 20);

                let isEditorScrolling = false;
                let isPreviewScrolling = false;

                editorInstance.onDidScrollChange((e) => {
                    if (!e.scrollTopChanged) return;
                    if (isPreviewScrolling) return; 
                    isEditorScrolling = true;
                    syncPreviewScroll();
                    setTimeout(() => isEditorScrolling = false, 50);
                });

                editPreview.addEventListener('scroll', () => {
                    if (isEditorScrolling) return;
                    isPreviewScrolling = true;
                    syncEditorScroll();
                    setTimeout(() => isPreviewScrolling = false, 50);
                });

            } catch (e) {
                console.error(e);
                showToast(e.message);
                setTimeout(() => window.location.href = '/', 1500);
            }
        });

        editCategorySelect.addEventListener('change', () => {
            if (editCategorySelect.value === '__NEW__') {
                editCategorySelect.style.display = 'none';
                editCategoryInput.style.display = 'block';
                editCategoryInput.focus();
            }
        });

        editCategoryInput.addEventListener('blur', () => {
            if (!editCategoryInput.value.trim()) {
                editCategoryInput.style.display = 'none';
                editCategorySelect.style.display = 'block';
                editCategorySelect.value = 'Default';
            }
        });

        btnSavePost.addEventListener('click', async () => {
            if (!editorInstance) return;

            const title = editTitle.value.trim();
            const description = editDescription ? editDescription.value.trim() : '';
            const context = editorInstance.getValue();
            let category = editCategorySelect.value;
            
            if (editCategoryInput.style.display !== 'none') {
                category = editCategoryInput.value.trim();
            }

            if (!title) return showToast('标题不能为空');
            if (category === '__NEW__' || !category) category = 'Default';

            btnSavePost.textContent = '保存中...';
            btnSavePost.disabled = true;

            try {
                const res = await fetch('/api/post/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': localStorage.getItem('mc_token')
                    },
                    body: JSON.stringify({
                        cid: cid,
                        title: title,
                        category: category,
                        context: context,
                        description: description
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    markClean(); // 标记已保存
                    
                    showToast('保存成功，正在跳转...');
                    setTimeout(() => {
                        // [修改] 跳转到文章页
                        if (data.url) {
                            window.location.href = data.url;
                        } else {
                            window.location.href = `/${localStorage.getItem('mc_username')}/index.html`; 
                        }
                    }, 1000);
                } else {
                    const err = await res.json();
                    showToast('保存失败: ' + (err.error || '未知错误'));
                    btnSavePost.textContent = '保存文章';
                    btnSavePost.disabled = false;
                }
            } catch (e) {
                showToast('网络错误');
                btnSavePost.textContent = '保存文章';
                btnSavePost.disabled = false;
            }
        });

        // [修改] 返回按钮逻辑：检查是否未保存
        btnBack.addEventListener('click', () => {
            if (isEditorDirty) {
                if (!confirm("您有未保存的更改，确定要离开吗？")) return;
            }
            window.history.back();
        });
    }

    // --- Delete Post Logic ---
    document.querySelectorAll('.btn-delete-post').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); 
            deleteTargetCid = btn.dataset.cid;
            if(deleteModal) deleteModal.classList.add('open');
        });
    });

    if (btnCancelDelete) {
        btnCancelDelete.addEventListener('click', () => {
            if(deleteModal) deleteModal.classList.remove('open');
            deleteTargetCid = null;
        });
    }

    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', async () => {
            if (!deleteTargetCid) return;
            
            btnConfirmDelete.textContent = '删除中...';
            btnConfirmDelete.disabled = true;

            try {
                const res = await fetch('/api/post/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': localStorage.getItem('mc_token')
                    },
                    body: JSON.stringify({ cid: deleteTargetCid })
                });

                if (res.ok) {
                    localStorage.setItem('mc_pending_toast', '文章已删除');
                    location.reload();
                } else {
                    const data = await res.json();
                    showToast('删除失败: ' + (data.error || '未知错误'));
                    btnConfirmDelete.textContent = '确认删除';
                    btnConfirmDelete.disabled = false;
                    deleteModal.classList.remove('open');
                }
            } catch (e) {
                showToast('网络错误');
                btnConfirmDelete.textContent = '确认删除';
                btnConfirmDelete.disabled = false;
                deleteModal.classList.remove('open');
            }
        });
    }


    if (btnCreatePost) {
        btnCreatePost.addEventListener('click', async () => {
            // 防止重复点击（保险）
            if (btnCreatePost.disabled) return;

            const originalText = btnCreatePost.textContent;
            btnCreatePost.disabled = true; // 立即禁用
            btnCreatePost.textContent = '创建中...';
            
            const startTime = Date.now();
            let success = false;

            try {
                const res = await fetch('/api/post/create', {
                    method: 'POST',
                    headers: { 'Authorization': localStorage.getItem('mc_token') }
                });
                
                // 强制冷却: 无论请求多快，至少等 1 秒
                const elapsed = Date.now() - startTime;
                if (elapsed < 1000) {
                    await new Promise(resolve => setTimeout(resolve, 1000 - elapsed));
                }

                if (res.ok) {
                    success = true;
                    // showToast('创建成功，正在跳转...'); // Remove or keep
                    localStorage.setItem('mc_pending_toast', '文章创建成功！'); // Add this
                    location.reload(); 
                } else {
                    showToast('创建失败');
                }
            } catch (e) {
                // 网络错误也要冷却
                const elapsed = Date.now() - startTime;
                if (elapsed < 1000) {
                    await new Promise(resolve => setTimeout(resolve, 1000 - elapsed));
                }
                showToast('网络错误');
            } finally {
                // 只有失败才恢复按钮，成功的话页面都要刷新了
                if (!success) {
                    btnCreatePost.disabled = false;
                    btnCreatePost.textContent = originalText;
                }
            }
        });
    }

    if (btnMigrateTrigger) {
        btnMigrateTrigger.addEventListener('click', () => {
            if (migrateModal) {
                migrateModal.classList.add('open');
                migrateInputArea.style.display = 'block';
                migrateProgressArea.style.display = 'none';
                migrateLogs.innerHTML = '';
                inpMigrateUrl.value = '';
                btnCloseMigrate.style.display = 'none';
                if (btnStopMigrate) btnStopMigrate.style.display = 'block';
            }
        });
    }

    if (btnCancelMigrate) {
        btnCancelMigrate.addEventListener('click', () => {
            if (migrateModal) migrateModal.classList.remove('open');
        });
    }

    if (btnStopMigrate) {
        btnStopMigrate.addEventListener('click', () => {
            if (migrateAbortController) {
                migrateAbortController.abort();
                const line = document.createElement('div');
                line.textContent = `> [操作] 用户已中止迁移。`;
                line.style.color = '#ef4444';
                migrateLogs.appendChild(line);
                migrateLogs.scrollTop = migrateLogs.scrollHeight;
                
                btnStopMigrate.style.display = 'none';
                
                const closeBtn = document.createElement('button');
                closeBtn.className = 'btn-action cancel'; 
                closeBtn.style.flex = '1';
                closeBtn.textContent = '关闭';
                closeBtn.onclick = () => location.reload();
                
                const actionContainer = btnCloseMigrate.parentElement;
                actionContainer.innerHTML = ''; 
                actionContainer.appendChild(closeBtn);
            }
        });
    }

    if (btnStartMigrate) {
        btnStartMigrate.addEventListener('click', async () => {
            const url = inpMigrateUrl.value.trim();
            if (!url) return showToast('请输入链接');

            migrateInputArea.style.display = 'none';
            migrateProgressArea.style.display = 'block';
            if (btnStopMigrate) btnStopMigrate.style.display = 'block';
            
            const log = (msg) => {
                const line = document.createElement('div');
                line.textContent = `> ${msg}`;
                migrateLogs.appendChild(line);
                migrateLogs.scrollTop = migrateLogs.scrollHeight;
            };

            log(`开始连接服务器...`);

            migrateAbortController = new AbortController();

            try {
                const response = await fetch('/api/post/migrate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': localStorage.getItem('mc_token')
                    },
                    body: JSON.stringify({ url }),
                    signal: migrateAbortController.signal
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split("\n\n");
                    buffer = lines.pop(); 

                    for (const line of lines) {
                        if (line.startsWith("data: ")) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                if (data.step) {
                                    log(data.step);
                                } else if (data.success) {
                                    log(`[成功] 文章已创建 (CID: ${data.cid})`);
                                    if (btnStopMigrate) btnStopMigrate.style.display = 'none';
                                    btnCloseMigrate.style.display = 'block';
                                } else if (data.error) {
                                    log(`[错误] ${data.error}`);
                                    log(`操作已终止。`);
                                    if (btnStopMigrate) btnStopMigrate.style.display = 'none';
                                    
                                    const retryBtn = document.createElement('button');
                                    retryBtn.className = 'btn-action cancel';
                                    retryBtn.style.flex = '1';
                                    retryBtn.textContent = '关闭';
                                    retryBtn.onclick = () => location.reload();
                                    
                                    const actionContainer = btnCloseMigrate.parentElement;
                                    actionContainer.innerHTML = '';
                                    actionContainer.appendChild(retryBtn);
                                }
                            } catch (e) {
                                console.error("Parse Error", e);
                            }
                        }
                    }
                }

            } catch (e) {
                if (e.name === 'AbortError') {
                } else {
                    log(`[网络错误] ${e.message}`);
                }
            } finally {
                migrateAbortController = null;
            }
        });
    }

    window.startAuth = async (platform) => {
        try {
            const token = localStorage.getItem('mc_token');
            const initRes = await fetch('/api/auth/init', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': token 
                },
                body: JSON.stringify({ platform })
            });
            
            if (!initRes.ok) throw new Error('启动失败');

            const initData = await initRes.json();
            currentSessionId = initData.session_id;
            
            showToast('正在启动验证客户端...');
            
            if (authEventSource) authEventSource.close();
            
            authEventSource = new EventSource(`/api/auth/watch?session_id=${currentSessionId}`);
            
            authEventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.status === 'authenticated') {
                    authEventSource.close();
                    authEventSource = null;
                    localStorage.setItem('mc_pending_toast', '绑定成功！');
                    location.reload();
                } else if (data.status === 'failed') {
                    authEventSource.close();
                    authEventSource = null;
                    showToast('绑定失败: ' + (data.error || '未知错误'));
                }
            };

            authEventSource.onerror = (err) => {
                if (authEventSource && authEventSource.readyState === EventSource.CLOSED) {
                } else {
                }
            };

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
                    } else {
                        showToast('无法连接到本地客户端，请确保客户端正在运行');
                        if (authEventSource) authEventSource.close();
                    }
                } catch (e) {
                    showToast('无法连接到本地客户端，请确保客户端正在运行\n' + 
                              '启动方式: python client/verifier.py --server ' + window.location.origin);
                    if (authEventSource) authEventSource.close();
                }
            }, 500);

        } catch (e) {
            showToast('错误: ' + e.message);
        }
    };

    if (btnCancelQr) {
        btnCancelQr.addEventListener('click', async () => {
            if (authEventSource) {
                authEventSource.close();
                authEventSource = null;
            }
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

    // [Modification] Logout immediately reloads page
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('mc_token');
            localStorage.removeItem('mc_username');
            document.cookie = "mc_token=; path=/; max-age=0";
            
            if (window.location.pathname.includes('settings') || window.location.pathname.includes('edit')) {
                window.location.href = '/';
            } else {
                location.reload();
            }
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
                    showToast('登录成功');
                    
                    setTimeout(() => {
                        window.location.href = `/${u}/index.html`;
                    }, 800);
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
                } else {
                    const errData = await res.json();
                    showToast(errData.error || '修改失败');
                }
            } catch (e) { 
                showToast('网络错误: ' + e.message); 
            }
        });
    }
});