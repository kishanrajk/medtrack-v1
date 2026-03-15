// --- State & Auth ---
let currentUser = null;
let currentView = 'dashboard';

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
    // Check Auth first
    if (!api.token) {
        showLogin();
    } else {
        try {
            currentUser = await api.getCurrentUser();
            initApp();
        } catch (e) {
            showLogin();
        }
    }

    // Login Form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
});

function showLogin() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('main-app').style.display = 'none';
}

function initApp() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('main-app').style.display = 'flex';
    document.getElementById('user-name').textContent = currentUser.name;

    // Show admin-only elements
    if (currentUser.role === 'admin') {
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'block');
    }

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = e.currentTarget.getAttribute('data-view');
            switchView(view);
        });
    });

    // Forms
    document.getElementById('add-equipment-form').addEventListener('submit', handleAddEquipment);
    document.getElementById('add-user-form').addEventListener('submit', handleAddUser);
    document.getElementById('repair-form').addEventListener('submit', handleReportRepair);
    document.getElementById('maintenance-form').addEventListener('submit', handleLogMaintenance);
    document.getElementById('resolve-repair-form').addEventListener('submit', handleResolveRepair);

    // Notifications
    const bell = document.getElementById('notif-bell');
    const drawer = document.getElementById('notif-drawer');
    bell.addEventListener('click', (e) => {
        e.stopPropagation();
        drawer.classList.toggle('active');
        if (drawer.classList.contains('active')) loadNotifications();
    });

    document.addEventListener('click', () => {
        drawer.classList.remove('active');
    });

    drawer.addEventListener('click', (e) => e.stopPropagation());

    // Settings
    const alertsToggle = document.getElementById('email-alerts-toggle');
    if (alertsToggle) {
        alertsToggle.addEventListener('change', async (e) => {
            try {
                await api.updatePrefs(e.target.checked);
            } catch (err) {
                alert("Failed to update preferences");
            }
        });
    }

    // Initial Load & Polling
    switchView('dashboard');
    refreshNotifications();
    setInterval(refreshNotifications, 30000);
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        await api.login(email, password);
        currentUser = await api.getCurrentUser();
        initApp();
    } catch (err) {
        alert("Login failed: " + err.message);
    }
}

function handleLogout() {
    api.logout();
}

function switchView(viewName, params = {}) {
    // Update active nav
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.getAttribute('data-view') === viewName);
    });

    // Hide all views
    const views = ['dashboard', 'registry', 'detail', 'settings', 'users'];
    views.forEach(v => {
        const el = document.getElementById(`view-${v}`);
        if (el) el.style.display = 'none';
    });

    // Show selected and load data
    const pageTitle = document.getElementById('page-title');
    const headerActions = document.getElementById('header-actions');
    headerActions.innerHTML = '';

    const viewEl = document.getElementById(`view-${viewName}`);
    if (viewEl) viewEl.style.display = 'block';

    if (viewName === 'dashboard') {
        pageTitle.textContent = 'Dashboard';
        headerActions.innerHTML = `<button class="btn btn-primary" onclick="openModal('add-equipment-modal')"><i class="fa-solid fa-plus"></i> Add Equipment</button>`;
        loadDashboard();
    } else if (viewName === 'registry') {
        pageTitle.textContent = 'Equipment Registry';
        headerActions.innerHTML = `<button class="btn btn-primary" onclick="openModal('add-equipment-modal')"><i class="fa-solid fa-plus"></i> Add Equipment</button>`;
        loadRegistry();
    } else if (viewName === 'detail') {
        pageTitle.textContent = 'Equipment Details';
        headerActions.innerHTML = `
            <button class="btn btn-outline" onclick="switchView('registry')"><i class="fa-solid fa-arrow-left"></i> Back</button>
            <button class="btn btn-warning" onclick="reportRepairModal(${params.id})"><i class="fa-solid fa-wrench"></i> Report Broken</button>
            <button class="btn btn-success" style="background:#22c55e;color:white" onclick="logMaintenanceModal(${params.id})"><i class="fa-solid fa-check"></i> Log Maint.</button>
        `;
        loadEquipmentDetail(params.id);
    } else if (viewName === 'settings') {
        pageTitle.textContent = 'Settings';
        loadSettings();
    } else if (viewName === 'users') {
        pageTitle.textContent = 'User Management';
        headerActions.innerHTML = `<button class="btn btn-primary" onclick="openModal('add-user-modal')"><i class="fa-solid fa-user-plus"></i> Add User</button>`;
        loadUsers();
    }
}

// --- Dashboard ---
async function loadDashboard() {
    try {
        const [equipment, upcomingMaint, activeRepairs, stats] = await Promise.all([
            api.getEquipment(),
            api.getUpcomingMaintenance(),
            api.getActiveRepairs(),
            api.getCostStats()
        ]);

        document.getElementById('kpi-active').textContent = equipment.filter(e => e.status === 'active').length;
        document.getElementById('kpi-repair').textContent = equipment.filter(e => e.status === 'under_repair').length;
        document.getElementById('kpi-maintenance').textContent = upcomingMaint.length;

        const repairsBody = document.getElementById('dashboard-repairs-body');
        repairsBody.innerHTML = activeRepairs.slice(0, 5).map(r => `
            <tr>
                <td><strong>EQ-${r.equipment_id}</strong></td>
                <td>${r.repair_date}</td>
                <td><span class="badge badge-repair">${r.status.replace('_', ' ')}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="3" class="text-center" style="color:var(--text-secondary)">No active repairs</td></tr>';

        const maintBody = document.getElementById('dashboard-maintenance-body');
        maintBody.innerHTML = upcomingMaint.slice(0, 5).map(m => `
            <tr>
                <td>${m.name} (${m.asset_id})</td>
                <td>${m.next_maintenance_date}</td>
                <td><button class="btn btn-outline" style="padding:0.25rem 0.5rem" onclick="switchView('detail', {id: ${m.id}})">View</button></td>
            </tr>
        `).join('') || '<tr><td colspan="3" class="text-center" style="color:var(--text-secondary)">No upcoming maintenance</td></tr>';

        renderCostChart(stats);

    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

// --- Registry ---
async function loadRegistry() {
    try {
        const data = await api.getEquipment();
        const tbody = document.getElementById('registry-body');
        tbody.innerHTML = data.map(item => `
            <tr style="cursor: pointer" onclick="switchView('detail', {id: ${item.id}})">
                <td><strong>${item.asset_id}</strong></td>
                <td>${item.name}</td>
                <td>${item.department}</td>
                <td>${getStatusBadge(item.status)}</td>
                <td>${item.next_maintenance_date}</td>
                <td><button class="btn btn-outline" style="padding:0.25rem 0.5rem">Details</button></td>
            </tr>
        `).join('');
    } catch (e) {
        console.error("Registry error:", e);
    }
}

// --- User Management ---
async function loadUsers() {
    try {
        const users = await api.getUsers();
        const tbody = document.getElementById('users-body');
        tbody.innerHTML = users.map(u => `
            <tr>
                <td>${u.name} ${u.id === currentUser.id ? '(You)' : ''}</td>
                <td>${u.email}</td>
                <td><span class="badge">${u.role}</span></td>
                <td>${u.is_active ? '<span class="text-success">Active</span>' : '<span class="text-danger">Inactive</span>'}</td>
                <td>
                    ${u.id !== currentUser.id ? `<button class="btn btn-outline" style="color:var(--error)" onclick="handleDeleteUser(${u.id})"><i class="fa-solid fa-trash"></i></button>` : ''}
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error("Users error:", e);
    }
}

async function handleDeleteUser(id) {
    if (!confirm("Are you sure you want to delete this user?")) return;
    try {
        await api.deleteUser(id);
        loadUsers();
    } catch (err) {
        alert("Delete failed");
    }
}

async function handleAddUser(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    try {
        await api.createUser(data);
        closeModal('add-user-modal');
        e.target.reset();
        loadUsers();
    } catch(err) {
        alert("Error adding user: " + err.message);
    }
}

// --- Other Utils & Actions ---
function getStatusBadge(status) {
    switch (status) {
        case 'active': return '<span class="badge badge-active">Active</span>';
        case 'under_repair': return '<span class="badge badge-repair">Under Repair</span>';
        default: return `<span class="badge badge-warning">${status}</span>`;
    }
}

function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

async function handleAddEquipment(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    data.maintenance_frequency_days = parseInt(data.maintenance_frequency_days);
    
    try {
        await api.createEquipment(data);
        closeModal('add-equipment-modal');
        e.target.reset();
        switchView(document.querySelector('.nav-link.active').getAttribute('data-view'));
    } catch(err) {
        alert("Error adding equipment: " + err.message);
    }
}

async function loadEquipmentDetail(id) {
    try {
        const item = await api.getEquipmentDetail(id);
        const container = document.getElementById('view-detail');
        container.innerHTML = `
            <div class="card mb-4">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <h2 style="font-size:1.75rem; margin-bottom:0.5rem;">${item.name}</h2>
                        <p style="color:var(--text-secondary)">${item.manufacturer} - ${item.model} | S/N: ${item.serial_number}</p>
                    </div>
                    ${getStatusBadge(item.status)}
                </div>
                <div class="grid-3 mt-4">
                    <div><p style="color:var(--text-secondary); font-size:0.875rem;">Department</p><p style="font-weight:600;">${item.department}</p></div>
                    <div><p style="color:var(--text-secondary); font-size:0.875rem;">Asset ID</p><p style="font-weight:600;">${item.asset_id}</p></div>
                    <div><p style="color:var(--text-secondary); font-size:0.875rem;">Next Maintenance</p><p style="font-weight:600; color:var(--warning);"><i class="fa-solid fa-clock"></i> ${item.next_maintenance_date}</p></div>
                </div>
            </div>
            <div class="grid-2">
                <div class="card">
                    <h3 style="margin-bottom:1rem;"><i class="fa-solid fa-clipboard-check text-success"></i> Maintenance History</h3>
                    <div class="table-container">
                        <table>
                            <thead><tr><th>Date</th><th>Performed By</th><th>Status</th><th>Cost</th></tr></thead>
                            <tbody>${item.maintenance_records.map(r => `<tr><td>${r.maintenance_date}</td><td>${r.performed_by}</td><td>${r.status}</td><td>${r.cost ? `₹${r.cost}` : '-'}</td></tr>`).join('') || '<tr><td colspan="4">No records</td></tr>'}</tbody>
                        </table>
                    </div>
                </div>
                <div class="card">
                    <h3 style="margin-bottom:1rem;"><i class="fa-solid fa-toolbox text-danger"></i> Repair History</h3>
                    <div class="table-container">
                        <table>
                            <thead><tr><th>Date</th><th>Issue</th><th>Status</th><th>Cost</th><th>Action</th></tr></thead>
                            <tbody>${item.repair_records.map(r => `<tr><td>${r.repair_date}</td><td>${r.issue_description}</td><td>${r.status}</td><td>${r.cost ? `₹${r.cost}` : '-'}</td><td>${r.status !== 'resolved' ? `<button class="btn btn-outline" style="padding:0.2rem 0.5rem" onclick="openResolveModal(${r.id}, ${item.id})">Resolve</button>` : ''}</td></tr>`).join('') || '<tr><td colspan="5">No records</td></tr>'}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    } catch(e) { console.error(e); }
}

function reportRepairModal(equipmentId) {
    document.getElementById('repair-equip-id').value = equipmentId;
    openModal('repair-modal');
}
async function handleReportRepair(e) {
    e.preventDefault();
    const equipId = document.getElementById('repair-equip-id').value;
    try {
        await api.reportRepair(equipId, {
            issue_description: document.getElementById('repair-description').value,
            repair_date: new Date().toISOString().split('T')[0],
            status: 'reported'
        });
        closeModal('repair-modal');
        loadEquipmentDetail(equipId);
    } catch(e) { alert("Fail"); }
}

function logMaintenanceModal(equipmentId) {
    document.getElementById('maint-equip-id').value = equipmentId;
    openModal('maintenance-modal');
}
async function handleLogMaintenance(e) {
    e.preventDefault();
    const equipId = document.getElementById('maint-equip-id').value;
    try {
        await api.logMaintenance(equipId, {
            maintenance_date: new Date().toISOString().split('T')[0],
            performed_by: document.getElementById('maint-performer').value,
            notes: document.getElementById('maint-notes').value,
            cost: document.getElementById('maint-cost').value ? parseFloat(document.getElementById('maint-cost').value) : null,
            status: 'completed'
        });
        closeModal('maintenance-modal');
        loadEquipmentDetail(equipId);
    } catch(e) { alert("Fail"); }
}

function openResolveModal(repairId, equipmentId) {
    document.getElementById('resolve-repair-id').value = repairId;
    document.getElementById('resolve-equip-id').value = equipmentId;
    document.getElementById('resolve-notes').value = '';
    document.getElementById('resolve-cost').value = '';
    openModal('resolve-repair-modal');
}

async function handleResolveRepair(e) {
    e.preventDefault();
    const repairId = document.getElementById('resolve-repair-id').value;
    const equipId = document.getElementById('resolve-equip-id').value;
    
    try {
        await api.resolveRepair(repairId, {
            technician_notes: document.getElementById('resolve-notes').value,
            cost: document.getElementById('resolve-cost').value ? parseFloat(document.getElementById('resolve-cost').value) : null
        });
        closeModal('resolve-repair-modal');
        loadEquipmentDetail(equipId);
    } catch(e) { alert("Error resolving repair"); }
}

// --- Notifications Polling ---
async function refreshNotifications() {
    try {
        const notifs = await api.getNotifications(true);
        const badge = document.getElementById('notif-count');
        badge.textContent = notifs.length;
        badge.style.display = notifs.length ? 'flex' : 'none';
    } catch(e) {}
}

async function loadNotifications() {
    try {
        const notifs = await api.getNotifications();
        document.getElementById('notif-list').innerHTML = notifs.map(n => `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="handleNotifClick(${n.id}, ${n.equipment_id})">
                <div class="notif-item-title">${n.title}</div>
                <div class="notif-item-msg">${n.message}</div>
            </div>
        `).join('') || '<p class="text-center" style="padding:1rem;">No notifications</p>';
    } catch(e) {}
}

async function handleNotifClick(id, equipId) {
    await api.markNotifRead(id);
    if (equipId) switchView('detail', {id: equipId});
    refreshNotifications();
}

async function markAllAsRead() {
    const notifs = await api.getNotifications(true);
    for (const n of notifs) {
        await api.markNotifRead(n.id);
    }
    loadNotifications();
    refreshNotifications();
}

async function loadSettings() {
    const prefs = await api.getUserPrefs();
    document.getElementById('email-alerts-toggle').checked = !!prefs.email_alerts_enabled;
}

let costChart = null;
function renderCostChart(data) {
    console.log('Rendering Chart with data:', data);
    if (!data || !data.labels) {
        console.error('Invalid chart data received');
        return;
    }
    const ctx = document.getElementById('costChart').getContext('2d');
    
    if (costChart) {
        costChart.destroy();
    }
    
    costChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Maintenance',
                    data: data.maintenance,
                    backgroundColor: '#10b981',
                    borderRadius: 4
                },
                {
                    label: 'Repairs',
                    data: data.repairs,
                    backgroundColor: '#ef4444',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        callback: (value) => '₹' + value
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 8
                    }
                }
            }
        }
    });
}
