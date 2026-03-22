/**
 * 管理后台模块
 */

// 全局变量 - 存储用户列表
let adminUsersList = [];

// 检查管理员权限
async function checkAdminAuth() {
    if (!Auth.isLoggedIn()) {
        window.location.href = 'admin-login.html';
        return false;
    }

    const user = Auth.getUser();
    if (!user || !user.is_admin) {
        alert('您没有管理员权限');
        Auth.logout();
        window.location.href = 'admin-login.html';
        return false;
    }

    document.getElementById('current-admin').textContent = user.username;
    return true;
}

// 管理员登出
function adminLogout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    window.location.href = 'admin-login.html';
}

// 初始化导航
function initNavigation() {
    const navItems = document.querySelectorAll('.admin-nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // 更新导航状态
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // 显示对应区块
            const section = item.dataset.section;
            document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'));
            document.getElementById(`section-${section}`).classList.add('active');

            // 加载数据
            loadSectionData(section);
        });
    });
}

// 加载区块数据
function loadSectionData(section) {
    switch (section) {
        case 'users':
            loadUsers();
            break;
        case 'positions':
            loadAllPositions();
            break;
    }
}

// 加载用户列表
async function loadUsers() {
    try {
        const response = await Auth.fetch('/api/v1/admin/users');
        const result = await response.json();

        if (result.success) {
            adminUsersList = result.data;
            renderUsersTable(result.data);
            updateUserFilter(result.data);
            updateUserSelect(result.data);
        }
    } catch (error) {
        console.error('加载用户失败:', error);
    }
}

// 渲染用户表格
function renderUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = '';

    users.forEach(user => {
        const statusTag = user.is_active
            ? '<span class="tag active">活跃</span>'
            : '<span class="tag inactive">禁用</span>';

        const roleTag = user.is_admin
            ? '<span class="tag admin">管理员</span>'
            : '<span class="tag">普通用户</span>';

        // 获取当前登录用户
        const currentUser = Auth.getUser();
        const isSelf = currentUser && user.id === currentUser.id;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${statusTag}</td>
            <td>${roleTag}</td>
            <td>${user.position_count}</td>
            <td>${user.trade_count}</td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-warning" onclick="toggleUserStatus(${user.id}, ${!user.is_active})" ${isSelf ? 'disabled' : ''}>
                    ${user.is_active ? '禁用' : '启用'}
                </button>
                <button class="btn btn-sm btn-secondary" onclick="showResetPasswordModal(${user.id})">重置密码</button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})" ${isSelf ? 'disabled' : ''}>删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// 更新用户筛选下拉框
function updateUserFilter(users) {
    const select = document.getElementById('admin-user-filter');
    if (!select) return;

    select.innerHTML = '<option value="">全部用户</option>';
    users.forEach(user => {
        select.innerHTML += `<option value="${user.id}">${user.username}</option>`;
    });
}

// 更新持仓模态框的用户选择
function updateUserSelect(users) {
    const select = document.getElementById('position-user-id');
    if (!select) return;

    select.innerHTML = '<option value="">选择用户</option>';
    users.forEach(user => {
        select.innerHTML += `<option value="${user.id}">${user.username}</option>`;
    });
}

// 切换用户状态
async function toggleUserStatus(userId, isActive) {
    if (!confirm(`确定要${isActive ? '启用' : '禁用'}该用户吗？`)) {
        return;
    }

    try {
        const response = await Auth.fetch(`/api/v1/admin/users/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });

        const result = await response.json();

        if (result.success) {
            loadUsers();
        } else {
            alert(result.message || '操作失败');
        }
    } catch (error) {
        console.error('操作失败:', error);
        alert('操作失败');
    }
}

// 删除用户
async function deleteUser(userId) {
    // 检查是否删除自己
    const currentUser = Auth.getUser();
    if (currentUser && userId === currentUser.id) {
        alert('不能删除自己的账户');
        return;
    }

    if (!confirm('确定要删除该用户吗？此操作将同时删除该用户的所有持仓和交易数据，且不可恢复！')) {
        return;
    }

    try {
        const response = await Auth.fetch(`/api/v1/admin/users/${userId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            loadUsers();
            alert('用户已删除');
        } else {
            alert(result.message || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}

// 显示重置密码模态框
function showResetPasswordModal(userId) {
    document.getElementById('reset-user-id').value = userId;
    document.getElementById('new-password').value = '123456';
    document.getElementById('reset-password-modal').classList.add('show');
}

// 关闭重置密码模态框
function closeResetPasswordModal() {
    document.getElementById('reset-password-modal').classList.remove('show');
}

// 确认重置密码
async function confirmResetPassword() {
    const userId = document.getElementById('reset-user-id').value;
    const newPassword = document.getElementById('new-password').value;

    try {
        const response = await Auth.fetch(`/api/v1/admin/users/${userId}/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_password: newPassword })
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);
            closeResetPasswordModal();
        } else {
            alert(result.message || '重置失败');
        }
    } catch (error) {
        console.error('重置失败:', error);
        alert('重置失败');
    }
}

// 加载所有持仓
async function loadAllPositions() {
    try {
        const response = await Auth.fetch('/api/v1/admin/positions');
        const result = await response.json();

        if (result.success) {
            renderPositionsTable(result.data.items);
        }
    } catch (error) {
        console.error('加载持仓失败:', error);
    }
}

// 按用户筛选持仓
async function filterPositionsByUser() {
    const userId = document.getElementById('admin-user-filter').value;

    try {
        let url = '/api/v1/admin/positions';
        if (userId) {
            url += `?user_id=${userId}`;
        }

        const response = await Auth.fetch(url);
        const result = await response.json();

        if (result.success) {
            renderPositionsTable(result.data.items);
        }
    } catch (error) {
        console.error('加载持仓失败:', error);
    }
}

// 渲染持仓表格
function renderPositionsTable(positions) {
    const tbody = document.getElementById('positions-table-body');
    tbody.innerHTML = '';

    positions.forEach(p => {
        const profitRate = p.profit_rate != null ? (p.profit_rate * 100).toFixed(2) : '--';
        const profitClass = p.profit_rate > 0 ? 'profit' : (p.profit_rate < 0 ? 'loss' : '');

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.id}</td>
            <td>${p.username || 'Unknown'}</td>
            <td>${p.name} (${p.symbol})</td>
            <td>${getAssetTypeLabel(p.asset_type)}</td>
            <td>${p.quantity}</td>
            <td>${p.cost_price}</td>
            <td>${p.current_price || '--'}</td>
            <td class="${profitClass}">${profitRate}%</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="editPosition(${p.id})">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deletePosition(${p.id})">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// 显示持仓模态框
async function showAdminPositionModal(positionId = null) {
    document.getElementById('position-id').value = '';
    document.getElementById('position-user-id').value = '';
    document.getElementById('position-symbol').value = '';
    document.getElementById('position-name').value = '';
    document.getElementById('position-asset-type').value = 'etf_index';
    document.getElementById('position-quantity').value = '';
    document.getElementById('position-cost-price').value = '';
    document.getElementById('position-current-price').value = '';
    document.getElementById('position-modal-title').textContent = '新增持仓';
    document.getElementById('position-modal').classList.add('show');
}

// 编辑持仓
async function editPosition(positionId) {
    try {
        const response = await Auth.fetch(`/api/v1/admin/positions/${positionId}`);
        const result = await response.json();

        if (result.success) {
            const p = result.data;
            document.getElementById('position-id').value = p.id;
            document.getElementById('position-user-id').value = p.user_id;
            document.getElementById('position-symbol').value = p.symbol;
            document.getElementById('position-name').value = p.name;
            document.getElementById('position-asset-type').value = p.asset_type;
            document.getElementById('position-quantity').value = p.quantity;
            document.getElementById('position-cost-price').value = p.cost_price;
            document.getElementById('position-current-price').value = p.current_price || '';
            document.getElementById('position-modal-title').textContent = '编辑持仓';
            document.getElementById('position-modal').classList.add('show');
        }
    } catch (error) {
        console.error('获取持仓失败:', error);
        alert('获取持仓失败');
    }
}

// 关闭持仓模态框
function closePositionModal() {
    document.getElementById('position-modal').classList.remove('show');
}

// 保存持仓
async function saveAdminPosition() {
    const positionId = document.getElementById('position-id').value;
    const data = {
        user_id: parseInt(document.getElementById('position-user-id').value),
        symbol: document.getElementById('position-symbol').value,
        name: document.getElementById('position-name').value,
        asset_type: document.getElementById('position-asset-type').value,
        quantity: parseInt(document.getElementById('position-quantity').value),
        cost_price: parseFloat(document.getElementById('position-cost-price').value),
        current_price: parseFloat(document.getElementById('position-current-price').value) || null
    };

    if (!data.user_id || !data.symbol || !data.name || !data.quantity || !data.cost_price) {
        alert('请填写完整信息');
        return;
    }

    try {
        let url = '/api/v1/admin/positions';
        let method = 'POST';

        if (positionId) {
            url = `/api/v1/admin/positions/${positionId}`;
            method = 'PUT';
        }

        const response = await Auth.fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            closePositionModal();
            loadAllPositions();
            alert(positionId ? '持仓更新成功' : '持仓创建成功');
        } else {
            alert(result.message || '操作失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败');
    }
}

// 删除持仓
async function deletePosition(positionId) {
    if (!confirm('确定要删除这个持仓吗？')) {
        return;
    }

    try {
        const response = await Auth.fetch(`/api/v1/admin/positions/${positionId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            loadAllPositions();
            alert('持仓已删除');
        } else {
            alert(result.message || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}

// 辅助函数
function formatDate(dateStr) {
    if (!dateStr) return '--';
    return dateStr.substring(0, 10);
}

function getAssetTypeLabel(type) {
    const labels = {
        'etf_index': '宽基ETF',
        'etf_sector': '行业ETF',
        'fund': '基金',
        'stock': '股票'
    };
    return labels[type] || type;
}

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    const isAuth = await checkAdminAuth();
    if (isAuth) {
        initNavigation();
        loadUsers();
    }
});