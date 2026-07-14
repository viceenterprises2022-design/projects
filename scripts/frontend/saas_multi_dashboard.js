document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = "";

    // Auth screen controls
    const authOverlay = document.getElementById('auth-overlay');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const btnShowRegister = document.getElementById('btn-show-register');
    const btnShowLogin = document.getElementById('btn-show-login');
    const authSubMsg = document.getElementById('auth-sub-msg');

    // Header controls
    const headerUserEmail = document.getElementById('header-user-email');
    const headerUserTier = document.getElementById('header-user-tier');
    const btnLogout = document.getElementById('btn-logout');

    // Metrics counters
    const metricLevLimit = document.getElementById('metric-lev-limit');
    const metricLevSub = document.getElementById('metric-lev-sub');
    const metricPositionsCount = document.getElementById('metric-positions-count');
    const metricTradesCount = document.getElementById('metric-trades-count');
    const metricRiskMult = document.getElementById('metric-risk-mult');

    // Tables & Log panels
    const positionsBody = document.getElementById('positions-body');
    const tradesBody = document.getElementById('trades-body');
    const auditLogContainer = document.getElementById('audit-log-container');
    const adminPanel = document.getElementById('admin-panel');
    const adminUsersBody = document.getElementById('admin-users-body');

    // Strategy & Credential Forms
    const credentialsForm = document.getElementById('credentials-form');
    const strategyForm = document.getElementById('strategy-form');
    const btnFireWebhook = document.getElementById('btn-fire-webhook');
    const btnTriggerAudit = document.getElementById('btn-trigger-audit');

    let pollInterval = null;
    let currentUserRole = "user";

    // Toggle Screen views
    btnShowRegister.addEventListener('click', () => {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        authSubMsg.textContent = "Register a new client vault account";
    });

    btnShowLogin.addEventListener('click', () => {
        registerForm.style.display = 'none';
        loginForm.style.display = 'block';
        authSubMsg.textContent = "Secure client verification portal";
    });

    // Check existing session token
    const savedToken = localStorage.getItem("SaaS_token");
    const savedEmail = localStorage.getItem("SaaS_email");
    const savedTier = localStorage.getItem("SaaS_tier");
    
    if (savedToken) {
        authOverlay.style.display = 'none';
        headerUserEmail.textContent = savedEmail;
        updateTierBadge(savedTier);
        startPolling();
    }

    // Login Form Submit
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            email: document.getElementById('login-email').value,
            password: document.getElementById('login-password').value
        };

        try {
            const res = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                localStorage.setItem("SaaS_token", data.token);
                localStorage.setItem("SaaS_email", data.email);
                localStorage.setItem("SaaS_tier", data.tier);
                
                headerUserEmail.textContent = data.email;
                updateTierBadge(data.tier);
                authOverlay.style.display = 'none';
                loginForm.reset();
                startPolling();
            } else {
                const err = await res.json();
                alert(err.detail || "Authentication failed.");
            }
        } catch (err) {
            alert(`Authentication network error: ${err}`);
        }
    });

    // Register Form Submit
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            email: document.getElementById('reg-email').value,
            password: document.getElementById('reg-password').value,
            tier: document.getElementById('reg-tier').value
        };

        try {
            const res = await fetch(`${API_BASE}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                alert("SaaS registration complete! You can now log in.");
                registerForm.reset();
                btnShowLogin.click();
            } else {
                const err = await res.json();
                alert(err.detail || "Registration failed.");
            }
        } catch (err) {
            alert(`Registration network error: ${err}`);
        }
    });

    // Logout
    btnLogout.addEventListener('click', () => {
        localStorage.removeItem("SaaS_token");
        localStorage.removeItem("SaaS_email");
        localStorage.removeItem("SaaS_tier");
        clearInterval(pollInterval);
        authOverlay.style.display = 'flex';
        adminPanel.style.display = 'none';
        headerUserEmail.textContent = "guest@alphaedge.com";
        updateTierBadge("free");
    });

    function updateTierBadge(tier) {
        headerUserTier.textContent = tier;
        headerUserTier.className = "tier-badge";
        if (tier === "enterprise") {
            headerUserTier.classList.add("tier-gold");
            metricLevLimit.textContent = "20x";
            metricLevSub.textContent = "Max leverage allowed";
        } else if (tier === "pro") {
            headerUserTier.classList.add("tier-pro");
            metricLevLimit.textContent = "15x";
            metricLevSub.textContent = "Max leverage allowed";
        } else {
            headerUserTier.classList.add("tier-free");
            metricLevLimit.textContent = "5x";
            metricLevSub.textContent = "Max leverage allowed";
        }
    }

    // Start Polling Dashboard Stats
    function startPolling() {
        fetchDashboardData();
        clearInterval(pollInterval);
        pollInterval = setInterval(fetchDashboardData, 3000);
    }

    async function fetchDashboardData() {
        const token = localStorage.getItem("SaaS_token");
        if (!token) return;

        // Try getting user dashboard first
        try {
            const res = await fetch(`${API_BASE}/api/user/dashboard`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.status === 401) {
                btnLogout.click();
                return;
            }
            if (res.ok) {
                const data = await res.json();
                currentUserRole = data.user.role;
                updateTierBadge(data.user.tier);
                
                if (currentUserRole === "admin") {
                    adminPanel.style.display = 'block';
                    fetchAdminDashboard(token);
                } else {
                    adminPanel.style.display = 'none';
                    updateUI(data);
                }
            }
        } catch (err) {
            console.error("Dashboard error:", err);
        }
    }

    async function fetchAdminDashboard(token) {
        try {
            const res = await fetch(`${API_BASE}/api/admin/dashboard`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                updateUI(data);
                renderAdminUsers(data.users);
            }
        } catch (err) {
            console.error("Admin dashboard fetch error:", err);
        }
    }

    // Populate positions and trades
    function updateUI(data) {
        metricPositionsCount.textContent = data.positions ? data.positions.length : 0;
        metricTradesCount.textContent = data.recent_trades ? data.recent_trades.length : 0;
        
        if (data.latest_audit) {
            metricRiskMult.textContent = `${data.latest_audit.daily_volatility_multiplier || 1.0}x`;
            renderAuditLog(data.latest_audit);
        } else {
            metricRiskMult.textContent = "1.0x";
        }

        // Positions
        positionsBody.innerHTML = "";
        if (data.positions && data.positions.length > 0) {
            data.positions.forEach(pos => {
                const tr = document.createElement('tr');
                const badge = pos.side === "LONG" ? "badge-long" : "badge-short";
                tr.innerHTML = `
                    <td>User #${pos.user_id}</td>
                    <td class="crypto-pair">${pos.symbol}</td>
                    <td><span class="${badge}">${pos.side}</span></td>
                    <td>${pos.size}</td>
                    <td>$${pos.entry_price.toLocaleString()}</td>
                    <td>${pos.leverage}x</td>
                    <td>
                        <span style="color: var(--accent-green)">TP: $${pos.tp_price ? pos.tp_price.toFixed(2) : '-'}</span> | 
                        <span style="color: var(--accent-red)">SL: $${pos.sl_price ? pos.sl_price.toFixed(2) : '-'}</span>
                    </td>
                `;
                positionsBody.appendChild(tr);
            });
        } else {
            positionsBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">No active positions found</td></tr>`;
        }

        // Trades
        tradesBody.innerHTML = "";
        if (data.recent_trades && data.recent_trades.length > 0) {
            data.recent_trades.forEach(trade => {
                const tr = document.createElement('tr');
                const badge = trade.side === "LONG" || trade.side === "BUY" ? "badge-long" : "badge-short";
                const timeStr = new Date(trade.timestamp).toLocaleTimeString();
                tr.innerHTML = `
                    <td>#${trade.id}</td>
                    <td>User #${trade.user_id}</td>
                    <td class="crypto-pair">${trade.symbol}</td>
                    <td><span class="${badge}">${trade.side}</span></td>
                    <td>$${trade.price.toLocaleString()}</td>
                    <td>${trade.size}</td>
                    <td>${trade.trigger_type}</td>
                    <td>${timeStr}</td>
                `;
                tradesBody.appendChild(tr);
            });
        } else {
            tradesBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-secondary);">No execution records</td></tr>`;
        }
    }

    function renderAuditLog(audit) {
        auditLogContainer.innerHTML = `
            <div style="color: var(--accent-cyan); margin-bottom: 0.5rem; font-weight: 600;">
                Audit #${audit.id} [${new Date(audit.timestamp).toLocaleTimeString()}]
            </div>
            <div style="margin-bottom: 0.5rem; color: #fff;">
                Leverage Ceiling: ${audit.suggested_leverage_limit}x | Volatility Mult: ${audit.daily_volatility_multiplier}x
            </div>
            <div style="white-space: pre-wrap; font-size: 0.8rem; color: #a4b3c6;">
                ${audit.audit_report}
            </div>
        `;
    }

    function renderAdminUsers(users) {
        adminUsersBody.innerHTML = "";
        if (users && users.length > 0) {
            users.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>User #${u.id}</td>
                    <td>${u.email}</td>
                    <td><span class="tier-badge">${u.tier}</span></td>
                `;
                adminUsersBody.appendChild(tr);
            });
        } else {
            adminUsersBody.innerHTML = `<tr><td colspan="3" style="text-align: center;">No registered clients</td></tr>`;
        }
    }

    // Credentials vault update
    credentialsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("SaaS_token");
        const payload = {
            broker_name: document.getElementById('cred-broker').value,
            api_key: document.getElementById('cred-key').value,
            api_secret: document.getElementById('cred-secret').value,
            wallet_address: document.getElementById('cred-wallet').value || null
        };

        try {
            const res = await fetch(`${API_BASE}/api/user/credentials`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                alert("Broker credentials securely updated and encrypted!");
                credentialsForm.reset();
            } else {
                const err = await res.json();
                alert(err.detail || "Failed to update keys.");
            }
        } catch (err) {
            alert(`Error: ${err}`);
        }
    });

    // Strategy Parameters Deploy
    strategyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("SaaS_token");
        const symbol = document.getElementById('strat-symbol').value;
        const payload = {
            symbol: symbol,
            asset_type: symbol === "GOLD-MCX" ? "commodity" : "crypto",
            active: true,
            leverage: parseInt(document.getElementById('strat-leverage').value),
            size_pct: parseFloat(document.getElementById('strat-size').value),
            stop_loss: parseFloat(document.getElementById('strat-sl').value),
            take_profit: parseFloat(document.getElementById('strat-tp').value)
        };

        try {
            const res = await fetch(`${API_BASE}/api/user/strategy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                alert("Strategy configurations successfully deployed!");
                strategyForm.reset();
                fetchDashboardData();
            } else {
                const err = await res.json();
                alert(err.detail || "Strategy config update failed.");
            }
        } catch (err) {
            alert(`Error: ${err}`);
        }
    });

    // Fire Mock Webhook trigger
    btnFireWebhook.addEventListener('click', async () => {
        const payload = {
            symbol: document.getElementById('web-symbol').value,
            action: document.getElementById('web-action').value,
            price: parseFloat(document.getElementById('web-price').value),
            size: parseFloat(document.getElementById('web-size').value),
            token: "supersecret_webhook_token"
        };

        try {
            const res = await fetch(`${API_BASE}/api/webhook/tradingview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                console.log("Mock TV alert fired.");
                setTimeout(fetchDashboardData, 800);
            } else {
                alert("Failed to trigger webhook simulator.");
            }
        } catch (err) {
            alert(`Error: ${err}`);
        }
    });

    // Trigger AI Audit Review
    btnTriggerAudit.addEventListener('click', async () => {
        const token = localStorage.getItem("SaaS_token");
        btnTriggerAudit.disabled = true;
        btnTriggerAudit.textContent = "Gemini Processing...";
        auditLogContainer.textContent = "AI Compliance Auditor is synthesizing trading metrics. Please wait...";

        try {
            const res = await fetch(`${API_BASE}/api/admin/audit`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                let count = 0;
                const check = setInterval(async () => {
                    await fetchDashboardData();
                    count++;
                    if (count > 5) {
                        clearInterval(check);
                        btnTriggerAudit.disabled = false;
                        btnTriggerAudit.textContent = "Run Gemini Offline Risk Audit";
                    }
                }, 2000);
            } else {
                const err = await res.json();
                auditLogContainer.textContent = `Audit failure: ${err.detail}`;
                btnTriggerAudit.disabled = false;
                btnTriggerAudit.textContent = "Run Gemini Offline Risk Audit";
            }
        } catch (err) {
            auditLogContainer.textContent = `Audit network error: ${err}`;
            btnTriggerAudit.disabled = false;
            btnTriggerAudit.textContent = "Run Gemini Offline Risk Audit";
        }
    });
});
