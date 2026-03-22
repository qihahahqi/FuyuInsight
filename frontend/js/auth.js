/**
 * 认证模块 - Token 管理与认证 API
 */

const Auth = {
    TOKEN_KEY: 'auth_token',
    USER_KEY: 'user_info',

    /**
     * 保存 Token
     */
    saveToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },

    /**
     * 获取 Token
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    /**
     * 保存用户信息
     */
    saveUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    /**
     * 获取用户信息
     */
    getUser() {
        const userStr = localStorage.getItem(this.USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    },

    /**
     * 检查是否已登录
     */
    isLoggedIn() {
        return !!this.getToken();
    },

    /**
     * 登出
     */
    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        window.location.href = 'login.html';
    },

    /**
     * 用户登录
     */
    async login(username, password) {
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();

        if (result.success) {
            this.saveToken(result.token);
            this.saveUser(result.user);
        }

        return result;
    },

    /**
     * 用户注册
     */
    async register(username, email, password) {
        const response = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });

        return await response.json();
    },

    /**
     * 获取当前用户信息
     */
    async getCurrentUser() {
        const response = await fetch('/api/v1/auth/me', {
            headers: this.getAuthHeaders()
        });

        return await response.json();
    },

    /**
     * 修改密码
     */
    async changePassword(oldPassword, newPassword) {
        const response = await fetch('/api/v1/auth/password', {
            method: 'PUT',
            headers: {
                ...this.getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });

        return await response.json();
    },

    /**
     * 获取认证请求头
     */
    getAuthHeaders() {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    /**
     * 带认证的 fetch 封装
     */
    async fetch(url, options = {}) {
        const authHeaders = this.getAuthHeaders();
        const headers = {
            ...options.headers,
            ...authHeaders
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        // 处理 401 未授权响应
        if (response.status === 401) {
            this.logout();
            return null;
        }

        return response;
    },

    /**
     * 检查登录状态，未登录则跳转
     */
    requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = 'login.html';
            return false;
        }
        return true;
    }
};

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Auth;
}