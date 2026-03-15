const API_BASE = '/api';

const api = {
    token: localStorage.getItem('token'),

    // --- Auth ---
    async login(email, password) {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }

        const data = await res.json();
        this.token = data.access_token;
        localStorage.setItem('token', this.token);
        return data;
    },

    logout() {
        this.token = null;
        localStorage.removeItem('token');
        location.reload();
    },

    async getCurrentUser() {
        return this.fetch('/auth/me');
    },

    // --- Users (Admin Only) ---
    async getUsers() {
        return this.fetch('/users/');
    },

    async createUser(userData) {
        return this.fetch('/users/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },

    async deleteUser(id) {
        return this.fetch(`/users/${id}`, {
            method: 'DELETE'
        });
    },

    // --- Equipment ---
    async getEquipment() {
        return this.fetch('/equipment/');
    },
    async getEquipmentDetail(id) {
        return this.fetch(`/equipment/${id}`);
    },
    async createEquipment(data) {
        return this.fetch('/equipment/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // --- Maintenance ---
    async getUpcomingMaintenance() {
        return this.fetch('/maintenance/upcoming');
    },
    async logMaintenance(equipmentId, data) {
        return this.fetch(`/maintenance/equipment/${equipmentId}`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // --- Repairs ---
    async getActiveRepairs() {
        return this.fetch('/repairs/');
    },
    async reportRepair(equipmentId, data) {
        return this.fetch(`/repairs/equipment/${equipmentId}`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async resolveRepair(repairId, data) {
        return this.fetch(`/repairs/${repairId}`, {
            method: 'PUT',
            body: JSON.stringify({ ...data, status: 'resolved' })
        });
    },

    // --- Notifications ---
    async getNotifications(unreadOnly = false) {
        return this.fetch(`/notifications/?unread_only=${unreadOnly}`);
    },
    async markNotifRead(id) {
        return this.fetch(`/notifications/${id}/read`, { method: 'PUT' });
    },

    // --- User Prefs ---
    async getUserPrefs() {
        return this.fetch('/notifications/user/preferences');
    },
    async updatePrefs(enabled) {
        return this.fetch(`/notifications/user/preferences?enabled=${enabled}`, { method: 'PUT' });
    },

    async getCostStats() {
        return this.fetch('/stats/costs');
    },

    // --- Fetch Wrapper ---
    async fetch(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const res = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (res.status === 401 && endpoint !== '/auth/login') {
            this.logout();
            throw new Error('Session expired');
        }

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(err.detail || 'Request failed');
        }

        return res.json();
    }
};

