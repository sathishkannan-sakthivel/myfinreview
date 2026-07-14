/**
 * FinReview UI Logic - 2026 Edition
 * Handles visual analytics, name resolution, and specialized formatting.
 */

// 1. Centralized Asset Database
const FUND_MAP = {}; // Will be used as a fast-access cache
let CACHED_STOCKS_DB = [];
let CACHED_MF_DB = [];

/**
 * Loads stocks and mutual funds from the backend API.
 */
let _dbInitialized = false;
async function initAssetDatabase() {
    if (_dbInitialized) return;
    
    // Don't fetch if on the auth page (no token yet)
    if (!localStorage.getItem('finreview_token')) {
        return;
    }

    try {
        // Primary Method: Fetch from the backend API
        const [apiStocksRes, apiMfRes] = await Promise.all([
            fetch(`${CONFIG.API_URL}/reference/stocks`),
            fetch(`${CONFIG.API_URL}/reference/mutualfunds`)
        ]);

        if (apiStocksRes.ok) {
            CACHED_STOCKS_DB = await apiStocksRes.json();

        } else {
            // Fallback for stocks

            const fallbackStocksRes = await fetch(`data/stocks.json`);
            if (fallbackStocksRes.ok) CACHED_STOCKS_DB = await fallbackStocksRes.json();
        }

        if (apiMfRes.ok) {
            const mfObj = await apiMfRes.json();
            // Convert object format to array format
            CACHED_MF_DB = Object.entries(mfObj).map(([symbol, data]) => ({
                symbol: symbol,
                name: data.name,
                nav: data.nav,
                updated_at: data.updated_at
            }));
            console.log(`Loaded ${CACHED_MF_DB.length} mutual funds from API.`);
        } else {
            // Fallback for mutual funds

            const fallbackMfRes = await fetch(`data/mutualfunds.json`);
            if (fallbackMfRes.ok) {
                const mfObj = await fallbackMfRes.json();
                CACHED_MF_DB = Object.entries(mfObj).map(([symbol, data]) => ({
                    symbol: symbol, name: data.name, nav: data.nav, updated_at: data.updated_at
                }));
            }
        }
        _dbInitialized = true;
    } catch (e) {

    }
}

// Check every 2 seconds if we need to init (until initialized)
const _dbInitInterval = setInterval(() => {
    if (_dbInitialized) {
        clearInterval(_dbInitInterval);
    } else {
        initAssetDatabase();
    }
}, 2000);

initAssetDatabase();

function resolveDisplayName(symbol) {
    if (!symbol) return "Unknown Asset";
    
    // 1. Check Fast Cache
    if (FUND_MAP[symbol]) return FUND_MAP[symbol];

    const sym = String(symbol).toUpperCase();

    // 2. Search Mutual Funds (Usually numeric symbols)
    const mf = CACHED_MF_DB.find(m => String(m.symbol) === sym);
    if (mf) {
        FUND_MAP[symbol] = mf.name;
        return mf.name;
    }

    // 3. Search Stocks
    const stock = CACHED_STOCKS_DB.find(s => s.symbol === sym || s.symbol === sym + ".NS" || s.symbol === sym + ".BO");
    if (stock) {
        FUND_MAP[symbol] = stock.name;
        return stock.name;
    }

    return symbol; // Fallback to symbol
}

// 2. Currency Formatting (Indian Standard)
function formatINR(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN', {
        maximumFractionDigits: 2,
        minimumFractionDigits: 2
    });
}

/**
 * Global Rupee Sanitizer
 * Replaces any instances of '$' or 'USD' with '₹' or 'INR' in dynamic strings.
 */
function sanitizeCurrency(text) {
    if (typeof text !== 'string') return text;
    return text.replace(/\$/g, '₹')
               .replace(/USD/g, 'INR')
               .replace(/dollars/gi, 'rupees');
}

/**
 * Basic Markdown to HTML Formatter
 * Handles **bold**, *italics*, and - bullet points.
 */
function formatMarkdown(text) {
    if (!text) return "";
    
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>');             // Italics
    
    // 1. Process Bullet Points separately to avoid <br> interference
    const lines = html.split('\n');
    let formattedLines = [];
    let inList = false;

    lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith('- ')) {
            if (!inList) {
                formattedLines.push('<ul class="ps-3 mt-2 mb-2">');
                inList = true;
            }
            formattedLines.push(`<li>${trimmed.substring(2)}</li>`);
        } else {
            if (inList) {
                formattedLines.push('</ul>');
                inList = false;
            }
            if (trimmed === "") {
                formattedLines.push('<div class="mb-2"></div>'); // Controlled spacing
            } else {
                formattedLines.push(`<div>${trimmed}</div>`);
            }
        }
    });
    
    if (inList) formattedLines.push('</ul>');

    return formattedLines.join('');
}

// 3. Visual Analytics (Chart.js)
let allocationChart = null;
const CHART_COLORS = [
    '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', 
    '#ec4899', '#f97316', '#64748b', '#14b8a6', '#a855f7'
];

function renderAllocationChart(holdings) {
    const canvas = document.getElementById('allocationChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Sort and limit for readability (Top 10 + Others)
    const sorted = [...holdings].sort((a, b) => b.current_valuation - a.current_valuation);
    const top10 = sorted.slice(0, 10);
    const othersVal = sorted.slice(10).reduce((sum, h) => sum + h.current_valuation, 0);
    
    const data = top10.map(h => h.current_valuation);
    const labels = top10.map(h => h.name || resolveDisplayName(h.symbol));
    const colors = CHART_COLORS.slice(0, top10.length);
    
    if (othersVal > 0) {
        data.push(othersVal);
        labels.push("Others");
        colors.push("#94a3b8"); // Distinct grey for 'Others'
    }

    if (allocationChart) allocationChart.destroy();

    allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const val = context.raw;
                            const pct = ((val / total) * 100).toFixed(1);
                            return ` ${context.label}: ${pct}%`;
                        }
                    }
                }
            },
            cutout: '75%'
        }
    });
}

// 8. Custom Toast Notification System
let toastInstance = null;

// Add CSS Fix for Dropdown Cursors and Pointer Events
const style = document.createElement('style');
style.innerHTML = `
    .dropdown-item, .cursor-pointer { cursor: pointer !important; }
    .btn { cursor: pointer !important; }
`;
document.head.appendChild(style);

function showToast(message, type = 'primary') {
    const toastEl = document.getElementById('liveToast');
    if (!toastEl) return;
    
    if (!toastInstance) {
        toastInstance = new bootstrap.Toast(toastEl, { delay: 3000 });
    }

    const toastBody = document.getElementById('toast-body');
    toastBody.innerText = message;
    
    // Update colors based on type
    const bgClass = type === 'success' ? 'bg-success text-white' : 
                   (type === 'danger' ? 'bg-danger text-white' : 
                   (type === 'warning' ? 'bg-warning text-dark' : 'bg-primary text-white'));
    
    toastEl.className = 'toast show shadow-lg border-0 ' + bgClass;
    const closeBtn = toastEl.querySelector('.btn-close');
    if (closeBtn) {
        closeBtn.className = 'btn-close me-2 m-auto ' + (type !== 'warning' ? 'btn-close-white' : '');
    }

    toastInstance.show();
}

// 9. Multi-Row Transaction Logic
let rowCount = 0;

function addTxRow(defaultData = {}) {
    const tbody = document.getElementById('tx-rows');
    const id = rowCount++;
    const row = document.createElement('tr');
    row.id = `tx-row-${id}`;
    
    row.innerHTML = `
        <td>
            <div class="tx-search-container">
                <input type="text" class="form-control form-control-sm tx-symbol-input" 
                       placeholder="Type 3 chars..." value="${defaultData.symbol || ''}" 
                       onkeyup="handleSearch(this.value, ${id})" required>
                <div id="results-${id}" class="tx-results-dropdown hidden"></div>
            </div>
        </td>
        <td>
            <select class="form-select form-select-sm tx-type-input">
                <option value="BUY" ${defaultData.type === 'BUY' ? 'selected' : ''}>BUY</option>
                <option value="SELL" ${defaultData.type === 'SELL' ? 'selected' : ''}>SELL</option>
            </select>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm tx-quantity-input" 
                   step="0.01" value="${defaultData.quantity || ''}" required>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm tx-price-input" 
                   step="0.01" value="${defaultData.price || ''}" required>
        </td>
        <td class="text-end">
            <button type="button" class="btn btn-outline-danger btn-sm border-0" onclick="removeTxRow(${id})">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                    <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                    <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                </svg>
            </button>
        </td>
    `;
    tbody.appendChild(row);
}

function removeTxRow(id) {
    const row = document.getElementById(`tx-row-${id}`);
    if (row) row.remove();
}

function downloadCSVTemplate() {
    const csvContent = "symbol,type,quantity,price\nRELIANCE.NS,BUY,10,2500.50\n120444,BUY,100,45.20";
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', 'finreview_template.csv');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// 4. Actionable Rebalancing Logic
function quickFillAction(symbol, action) {
    showPage('add-tx');
    
    // 1. Resolve Friendly Name for visible input
    const friendlyName = resolveDisplayName(symbol);
    document.getElementById('tx-symbol').value = friendlyName;
    
    // 2. Set Hidden Symbol for processing
    document.getElementById('tx-symbol-hidden').value = symbol;
    
    document.getElementById('tx-type').value = action;
    
    const form = document.getElementById('tx-form');
    let notes = document.getElementById('tx-notes');
    if (!notes) {
        const div = document.createElement('div');
        div.className = 'mb-3';
        div.innerHTML = '<label class="form-label small">Notes</label><textarea id="tx-notes" class="form-control" rows="2"></textarea>';
        form.insertBefore(div, form.querySelector('button'));
        notes = document.getElementById('tx-notes');
    }
    notes.value = "Automated suggestion for target weight alignment.";
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 5. Dynamic Asset Search (Autocomplete)
let searchTimeout = null;

async function handleSearch(query, rowId = null) {
    // Determine target container (row-specific, 'alert', or legacy fallback)
    const containerId = (rowId === 'alert') ? 'results-alert' : (rowId !== null ? `results-${rowId}` : 'search-results');
    const container = document.getElementById(containerId);
    if (!container) return;

    const qRaw = (query || '').trim();
    if (qRaw.length < 2) {
        container.classList.add('hidden');
        return;
    }

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        container.innerHTML = '<div class="list-group-item small text-center">Searching...</div>';
        container.classList.remove('hidden');

        try {
            let allResults = [];

            if (rowId === 'target') {
                // Filter from user's current holdings only
                const searchQ = qRaw.toUpperCase();
                allResults = GLOBAL_HOLDINGS.filter(h => 
                    h.symbol.toUpperCase().includes(searchQ) || 
                    (h.name && h.name.toUpperCase().includes(searchQ))
                ).map(h => ({
                    symbol: h.symbol,
                    name: h.name || resolveDisplayName(h.symbol),
                    type: h.symbol.match(/^\d+$/) ? 'MUTUAL_FUND' : 'STOCK'
                }));
            } else {
                const [mfResults, stockResults] = await Promise.all([
                    searchMutualFunds(qRaw).catch(() => []),
                    searchStocks(qRaw)
                ]);

                const searchQ = qRaw.toUpperCase();
                const sortFn = (a, b) => {
                    const aName = (a.name || '').toUpperCase();
                    const aSym = String(a.symbol || '').toUpperCase().replace('.NS', '').replace('.BO', '');
                    const bName = (b.name || '').toUpperCase();
                    const bSym = String(b.symbol || '').toUpperCase().replace('.NS', '').replace('.BO', '');
                    if (aSym === searchQ && bSym !== searchQ) return -1;
                    if (bSym === searchQ && aSym !== searchQ) return 1;
                    return aName.localeCompare(bName);
                };
                allResults = [...stockResults.sort(sortFn), ...mfResults.sort(sortFn)].slice(0, 15);
            }

            renderSearchResults(allResults, rowId);
        } catch (error) {
            console.error("Search error:", error);
            container.innerHTML = '<div class="list-group-item small text-danger">Search failed.</div>';
        }
    }, 200);
}

async function searchMutualFunds(query) {
    try {
        const res = await fetch(`https://api.mfapi.in/mf/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        return (data || []).map(item => ({
            symbol: item.schemeCode,
            name: item.schemeName,
            type: 'MUTUAL_FUND'
        }));
    } catch (e) { return []; }
}

function searchStocks(query) {
    const q = query.toUpperCase().trim();
    if (!q) return [];
    
    const keywords = q.split(/\s+/).filter(k => k.length > 0);
    const results = [];
    const db = CACHED_STOCKS_DB || [];
    
    // Performance Optimized Loop: Stop after 100 matches to keep UI responsive
    for (let i = 0; i < db.length; i++) {
        const s = db[i];
        if (!s) continue;
        
        const name = (s.name || '').toUpperCase();
        const symbol = (s.symbol || '').toUpperCase();
        
        const isMatch = keywords.every(k => name.includes(k) || symbol.includes(k));
        
        if (isMatch) {
            results.push({
                symbol: s.symbol,
                name: s.name,
                type: 'STOCK'
            });
            if (results.length >= 100) break; 
        }
    }
    return results;
}

function renderSearchResults(results, rowId = null) {
    const containerId = (rowId === 'alert') ? 'results-alert' : (rowId !== null ? `results-${rowId}` : 'search-results');
    const container = document.getElementById(containerId);
    if (!container) return;

    if (results.length === 0) {
        container.innerHTML = '<div class="list-group-item small text-muted">No matches found.</div>';
        return;
    }

    // Position detection for dynamic rows, alerts or target search
    if (rowId !== null) {
        let input;
        if (rowId === 'alert') {
            input = document.getElementById('alert-symbol-search');
        } else if (rowId === 'target') {
            input = document.getElementById('target-sym-search');
        } else {
            input = document.querySelector(`#tx-row-${rowId} .tx-symbol-input`);
        }

        if (input) {
            const rect = input.getBoundingClientRect();
            container.style.position = 'fixed';
            container.style.top = `${rect.bottom}px`;
            container.style.left = `${rect.left}px`;
            container.style.width = `${rect.width}px`;
        }
    }

    container.innerHTML = results.map(item => {
        const cleanName = item.name.replace(/'/g, "\\'");
        const rId = (typeof rowId === 'string') ? `'${rowId}'` : rowId;
        return `
            <div class="list-group-item list-group-item-action py-2 border-bottom cursor-pointer" 
                 style="font-size: 13px;"
                 onclick="event.preventDefault(); event.stopImmediatePropagation(); selectAsset('${item.symbol}', '${cleanName}', ${rId}); return false;">
                <div class="d-flex justify-content-between align-items-center mb-0">
                    <div class="fw-bold text-dark text-truncate" style="max-width: 70%;">${item.name}</div>
                    <span class="badge bg-light text-dark border" style="font-size: 8px;">${item.type}</span>
                </div>
                <div class="small text-muted" style="font-size: 10px;">${item.symbol}</div>
            </div>
        `;
    }).join('');
}

function selectAsset(symbol, name, rowId = null) {

    if (rowId === 'alert') {
        const symInput = document.getElementById('alert-symbol-search');
        if (symInput) symInput.value = name;
        const symHidden = document.getElementById('alert-symbol');
        if (symHidden) symHidden.value = symbol;
        const container = document.getElementById('results-alert');
        if (container) container.classList.add('hidden');
    } else if (rowId === 'target') {
        const symInput = document.getElementById('target-sym-search');
        if (symInput) symInput.value = name;
        const symHidden = document.getElementById('target-sym');
        if (symHidden) symHidden.value = symbol;
        const container = document.getElementById('results-target');
        if (container) container.classList.add('hidden');
    } else if (rowId !== null) {
        const row = document.getElementById(`tx-row-${rowId}`);
        if (row) {
            row.querySelector('.tx-symbol-input').value = symbol;
            const container = document.getElementById(`results-${rowId}`);
            if (container) container.classList.add('hidden');
        }
    }
    
    FUND_MAP[symbol] = name;
}

// Ensure global access
window.selectAsset = selectAsset;

// 6. AI Briefing Dismissal
function dismissAIBriefing() {
    const card = document.getElementById('ai-briefing-card');
    if (card) card.classList.add('hidden');
}

function openBriefingModal() {
    const modalEl = document.getElementById('briefingModal');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

function applyCommunityAccessStyles() {
    document.querySelectorAll('[data-community-hidden]').forEach(el => el.remove());
}

// 7. Notification Hub Logic
let NOTIFICATIONS = [];

function toggleNotifications() {
    const dropdown = document.getElementById('notif-dropdown');
    dropdown.classList.toggle('hidden');
    
    // Mark as seen when opened
    if (!dropdown.classList.contains('hidden')) {
        document.getElementById('notif-badge').classList.add('hidden');
    }
}

function addNotification(type, content) {
    const timestamp = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    NOTIFICATIONS.unshift({ type, content, time: timestamp });
    renderNotifications();
    
    // Show count on badge
    const badge = document.getElementById('notif-badge');
    if (badge) {
        badge.classList.remove('hidden');
        badge.innerText = NOTIFICATIONS.length;
    }
}

function renderNotifications() {
    const list = document.getElementById('notif-list');
    const count = document.getElementById('notif-count');
    
    if (NOTIFICATIONS.length === 0) {
        list.innerHTML = '<div class="text-center p-4 text-muted small">No recent signals.</div>';
        count.innerText = "0 New";
        return;
    }

    count.innerText = `${NOTIFICATIONS.length} Recent`;
    list.innerHTML = NOTIFICATIONS.map(n => `
        <div class="p-3 border-bottom hover-bg-light">
            <div class="d-flex justify-content-between mb-1">
                <span class="badge ${n.type.includes('RISK') ? 'badge-soft-danger' : 'badge-soft-primary'}" style="font-size: 9px;">${n.type.replace('_', ' ')}</span>
                <small class="text-muted" style="font-size: 10px;">${n.time}</small>
            </div>
            <div class="small text-dark" style="line-height: 1.4;">${n.content}</div>
        </div>
    `).join('');
}

// Close notifications when clicking outside
document.addEventListener('click', (e) => {
    const nav = document.querySelector('.bi-bell')?.parentElement;
    const dropdown = document.getElementById('notif-dropdown');
    if (nav && !nav.contains(e.target) && dropdown && !dropdown.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});
