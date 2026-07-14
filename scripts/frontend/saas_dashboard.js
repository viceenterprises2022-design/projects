document.addEventListener('DOMContentLoaded', () => {
    // API base URL is same host
    const API_BASE = "";

    // Poll interval
    const POLL_INTERVAL = 3000;

    // Elements
    const valClients = document.getElementById('val-clients');
    const valPositions = document.getElementById('val-positions');
    const valTrades = document.getElementById('val-trades');
    const valRisk = document.getElementById('val-risk');

    const positionsBody = document.getElementById('positions-body');
    const tradesBody = document.getElementById('trades-body');
    const auditLogContainer = document.getElementById('audit-log-container');

    const registerForm = document.getElementById('register-form');
    const strategyForm = document.getElementById('strategy-form');
    const btnFireWebhook = document.getElementById('btn-fire-webhook');
    const btnTriggerAudit = document.getElementById('btn-trigger-audit');

    // Fetch dashboard data
    async function fetchDashboard() {
        try {
            const res = await fetch(`${API_BASE}/api/dashboard`);
            if (!res.ok) throw new Error("Dashboard fetch failed");
            const data = await res.json();
            updateUI(data);
        } catch (err) {
            console.error("Error fetching dashboard data:", err);
        }
    }

    // Update HTML with response data
    function updateUI(data) {
        // Set metrics
        valClients.textContent = data.active_users_count || 0;
        valPositions.textContent = data.positions ? data.positions.length : 0;
        valTrades.textContent = data.recent_trades ? data.recent_trades.length : 0;
        
        if (data.latest_audit) {
            valRisk.textContent = `${data.latest_audit.daily_volatility_multiplier || 1.0}x`;
            renderAuditLog(data.latest_audit);
        } else {
            valRisk.textContent = "1.0x";
        }

        // Render positions
        positionsBody.innerHTML = "";
        if (data.positions && data.positions.length > 0) {
            data.positions.forEach(pos => {
                const tr = document.createElement('tr');
                const badgeClass = pos.side === 'LONG' ? 'badge-long' : 'badge-short';
                
                tr.innerHTML = `
                    <td>User #${pos.user_id}</td>
                    <td class="crypto-pair">${pos.symbol}</td>
                    <td><span class="${badgeClass}">${pos.side}</span></td>
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
            positionsBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">No active positions</td></tr>`;
        }

        // Render trades
        tradesBody.innerHTML = "";
        if (data.recent_trades && data.recent_trades.length > 0) {
            data.recent_trades.forEach(trade => {
                const tr = document.createElement('tr');
                const badgeClass = trade.side === 'BUY' || trade.side === 'LONG' ? 'badge-long' : 'badge-short';
                const timeString = new Date(trade.timestamp).toLocaleTimeString();
                
                tr.innerHTML = `
                    <td>#${trade.id}</td>
                    <td>User #${trade.user_id}</td>
                    <td class="crypto-pair">${trade.symbol}</td>
                    <td><span class="${badgeClass}">${trade.side}</span></td>
                    <td>$${trade.price.toLocaleString()}</td>
                    <td>${trade.size}</td>
                    <td>${trade.trigger_type}</td>
                    <td>${timeString}</td>
                `;
                tradesBody.appendChild(tr);
            });
        } else {
            tradesBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-secondary);">No execution logs</td></tr>`;
        }
    }

    // Render Gemini Audit Reports
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

    // Register User Form Submit
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            email: document.getElementById('reg-email').value,
            hl_wallet: document.getElementById('reg-wallet').value,
            hl_api_key: document.getElementById('reg-apikey').value,
            hl_api_secret: document.getElementById('reg-secret').value,
            risk_multiplier: parseFloat(document.getElementById('reg-risk').value),
            max_leverage: 10
        };

        try {
            const res = await fetch(`${API_BASE}/api/user/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                alert("Account vault successfully deployed!");
                registerForm.reset();
                fetchDashboard();
            } else {
                const errData = await res.json();
                alert(`Error: ${errData.detail}`);
            }
        } catch (err) {
            alert(`Network error: ${err}`);
        }
    });

    // Strategy Form Submit
    strategyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            user_id: parseInt(document.getElementById('strat-userid').value),
            symbol: document.getElementById('strat-symbol').value.toUpperCase(),
            active: true,
            size_pct: parseFloat(document.getElementById('strat-size').value),
            stop_loss: parseFloat(document.getElementById('strat-sl').value),
            take_profit: parseFloat(document.getElementById('strat-tp').value)
        };

        try {
            const res = await fetch(`${API_BASE}/api/user/strategy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                alert("Strategy mapping successfully updated!");
                strategyForm.reset();
                fetchDashboard();
            } else {
                const errData = await res.json();
                alert(`Error: ${errData.detail}`);
            }
        } catch (err) {
            alert(`Network error: ${err}`);
        }
    });

    // Fire Mock Webhook Button click
    btnFireWebhook.addEventListener('click', async () => {
        const payload = {
            symbol: document.getElementById('web-symbol').value.toUpperCase(),
            action: document.getElementById('web-action').value,
            price: parseFloat(document.getElementById('web-price').value),
            size: parseFloat(document.getElementById('web-size').value),
            token: "supersecret_webhook_token" // matches backend WEBHOOK_SECRET_TOKEN default
        };

        try {
            const res = await fetch(`${API_BASE}/api/webhook/tradingview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                const data = await res.json();
                console.log("Mock Webhook triggered:", data);
                // Trigger quick dashboard reload
                setTimeout(fetchDashboard, 500);
            } else {
                alert("Failed to send webhook. Check token config.");
            }
        } catch (err) {
            alert(`Network error: ${err}`);
        }
    });

    // Run AI compliance audit button click
    btnTriggerAudit.addEventListener('click', async () => {
        btnTriggerAudit.disabled = true;
        btnTriggerAudit.textContent = "Analyzing...";
        auditLogContainer.innerHTML = "Gemini is auditing trades and risk regimes. Please wait...";
        
        try {
            const res = await fetch(`${API_BASE}/api/admin/audit`, { method: 'POST' });
            if (res.ok) {
                // Poll check for new audit data in next few seconds
                let checkCount = 0;
                const checkInterval = setInterval(async () => {
                    await fetchDashboard();
                    checkCount++;
                    if (checkCount > 5) {
                        clearInterval(checkInterval);
                        btnTriggerAudit.disabled = false;
                        btnTriggerAudit.textContent = "Run Gemini Review";
                    }
                }, 2000);
            } else {
                const errData = await res.json();
                auditLogContainer.innerHTML = `Audit failed to trigger: ${errData.detail}`;
                btnTriggerAudit.disabled = false;
                btnTriggerAudit.textContent = "Run Gemini Review";
            }
        } catch (err) {
            auditLogContainer.innerHTML = `Audit trigger network error: ${err}`;
            btnTriggerAudit.disabled = false;
            btnTriggerAudit.textContent = "Run Gemini Review";
        }
    });

    // Initial load
    fetchDashboard();
    // Start interval
    setInterval(fetchDashboard, POLL_INTERVAL);
});
