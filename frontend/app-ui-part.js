function updateUI(data) {
    const user = localStorage.getItem('finreview_user') || 'Guest';
    const userDisplay = document.getElementById('user-display');
    if (userDisplay) userDisplay.innerText = user;
    
    // Snapshot
    document.getElementById('total-val').innerText = formatINR(data.total_valuation || 0);
    const gain = data.total_gain_loss || 0;
    const gainPct = data.total_gain_loss_pct || 0;
    const gainEl = document.getElementById('total-gain');
    gainEl.innerText = `${formatINR(gain)} (${gainPct.toFixed(2)}%)`;
    gainEl.className = `stat-val ${gain >= 0 ? 'text-success' : 'text-danger'}`;
    
    const xirr = (data.analytics?.xirr || 0);
    const xirrEl = document.getElementById('total-xirr');
    xirrEl.innerText = `${xirr.toFixed(2)}%`;
    xirrEl.className = `stat-val ${xirr >= 0 ? 'text-success' : 'text-danger'}`;

    if (data.holdings) renderAllocationChart(data.holdings);

    // AI Insights
    const insightList = document.getElementById('ai-insights-list');
    insightList.innerHTML = '';
    if (data.ai_insights && Object.keys(data.ai_insights).length > 0) {
        Object.entries(data.ai_insights).forEach(([type, insight]) => {
            const div = document.createElement('div');
            div.className = 'insight-item p-2 mb-2 rounded bg-white border';
            const badgeClass = type.includes('RISK') ? 'badge-soft-danger' : 'badge-soft-primary';
            div.innerHTML = `<span class="badge ${badgeClass} me-2">${type.replace(/_/g, ' ')}</span> ${insight.content}`;
            insightList.appendChild(div);
        });
    } else {
        insightList.innerText = "No intelligence signals. Click Refresh Intelligence.";
    }

    const sortedHoldings = [...(data.holdings || [])].sort((a, b) => (b.current_valuation || 0) - (a.current_valuation || 0));

    // Dashboard Top Holdings
    const tbody = document.getElementById('holdings-body');
    tbody.innerHTML = '';
    sortedHoldings.slice(0, 5).forEach(h => {
        const row = document.createElement('tr');
        const displayName = h.name || resolveDisplayName(h.symbol);
        row.innerHTML = `<td class="ps-3"><b>${displayName}</b><br><small class="text-muted">${h.symbol}</small></td>
                         <td>${h.total_quantity}</td>
                         <td>${formatINR(h.avg_price)}</td>
                         <td class="fw-bold">${formatINR(h.current_valuation || 0)}</td>
                         <td class="text-end pe-3"><span class="badge ${h.gain_loss_pct >= 0 ? 'badge-soft-success' : 'badge-soft-danger'}">${h.gain_loss_pct?.toFixed(2)}%</span></td>`;
        tbody.appendChild(row);
    });

    // Portfolio Performance Page
    const fullBody = document.getElementById('full-portfolio-body');
    if (fullBody) {
        fullBody.innerHTML = '';
        document.getElementById('port-total-val').innerText = formatINR(data.total_valuation || 0);
        const pGain = data.total_gain_loss || 0;
        const pGainPct = data.total_gain_loss_pct || 0;
        const pGainEl = document.getElementById('port-total-gain');
        pGainEl.innerText = `${formatINR(pGain)} (${pGainPct.toFixed(2)}%)`;
        pGainEl.className = `fw-bold h5 mb-0 ${pGain >= 0 ? 'text-success' : 'text-danger'}`;

        sortedHoldings.forEach(h => {
            const row = document.createElement('tr');
            const ltp = h.total_quantity > 0 ? (h.current_valuation / h.total_quantity) : 0;
            const absolutePL = (h.current_valuation || 0) - (h.total_quantity * h.avg_price);
            const displayName = h.name || resolveDisplayName(h.symbol);
            row.innerHTML = `<td class="ps-4"><b>${displayName}</b><br><small class="text-muted">${h.symbol}</small></td>
                             <td>${h.total_quantity}</td><td>${formatINR(h.avg_price)}</td><td>${formatINR(ltp)}</td>
                             <td>${formatINR(h.total_quantity * h.avg_price)}</td><td>${formatINR(h.current_valuation)}</td>
                             <td class="text-end pe-4">
                                <div class="fw-bold ${absolutePL >= 0 ? 'text-success' : 'text-danger'}">${formatINR(absolutePL)}</div>
                                <span class="badge ${h.gain_loss_pct >= 0 ? 'badge-soft-success' : 'badge-soft-danger'}">${h.gain_loss_pct?.toFixed(2)}%</span>
                             </td>`;
            fullBody.appendChild(row);
        });
    }

    // --- MARKET NEWS (Enhanced Tile Design) ---
    const newsList = document.getElementById('news-list');
    const newsGrid = document.getElementById('full-news-grid');
    
    if (newsList) {
        newsList.innerHTML = '';
        const newsItems = data.latest_news_list || [];
        
        if (newsItems.length > 0) {
            const groupedNews = {};
            newsItems.forEach(a => {
                if (!groupedNews[a.symbol]) groupedNews[a.symbol] = [];
                groupedNews[a.symbol].push(a);
            });

            // Dashboard View
            Object.entries(groupedNews).forEach(([symbol, articles]) => {
                const item = document.createElement('div');
                item.className = 'news-item py-2 border-bottom';
                item.innerHTML = `<div class="d-flex justify-content-between align-items-center mb-1">
                                    <small class="fw-bold text-primary">${resolveDisplayName(symbol)}</small>
                                    <span class="badge bg-light text-dark" style="font-size: 9px;">${articles.length} updates</span>
                                 </div>
                                 <div class="small text-truncate text-dark">${articles[0].title}</div>`;
                item.onclick = () => showPage('news');
                item.style.cursor = 'pointer';
                newsList.appendChild(item);
            });

            // News Page: Big Tile Design
            if (newsGrid) {
                newsGrid.innerHTML = Object.entries(groupedNews).map(([symbol, articles]) => `
                    <div class="col-md-12 col-lg-6">
                        <div class="card h-100 shadow-sm border-0" style="border-radius: 16px;">
                            <div class="card-header bg-white pt-4 border-0">
                                <h5 class="fw-bold text-dark mb-0">${resolveDisplayName(symbol)}</h5>
                                <small class="text-muted">${symbol}</small>
                            </div>
                            <div class="card-body">
                                <div class="list-group list-group-flush">
                                    ${articles.map(a => `
                                        <a href="${a.link}" target="_blank" class="list-group-item list-group-item-action border-0 px-0 py-3 d-flex justify-content-between align-items-center">
                                            <div class="pe-3">
                                                <div class="small text-dark mb-1" style="line-height: 1.4;">${a.title}</div>
                                                <small class="text-muted" style="font-size: 10px;">${new Date(a.published_at).toLocaleDateString('en-IN')}</small>
                                            </div>
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#3b82f6" class="bi bi-arrow-right-short flex-shrink-0" viewBox="0 0 16 16">
                                                <path fill-rule="evenodd" d="M4 8a.5.5 0 0 1 .5-.5h5.793L8.146 5.354a.5.5 0 1 1 .708-.708l3 3a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708-.708L10.293 8.5H4.5A.5.5 0 0 1 4 8"/>
                                            </svg>
                                        </a>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        } else {
            const emptyMsg = '<div class="text-muted text-center py-3">No news. Click Refresh Intelligence.</div>';
            if (newsList) newsList.innerHTML = emptyMsg;
            if (newsGrid) newsGrid.innerHTML = emptyMsg;
        }
    }
}
