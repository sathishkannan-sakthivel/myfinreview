// --- FINREVIEW GLOBAL CONFIGURATION ---
const CONFIG = {
    API_URL: window.FINREVIEW_API_URL || 'http://localhost:8000',
    CURRENCY_SYMBOL: '₹',
    USER_POOL_ID: 'us-east-1_XXXXX',
    CLIENT_ID: 'XXXXX'
};

// Sample data used only by local fallback utilities
const INITIAL_MOCK_DATA = {
    "total_valuation": 448765.00,
    "total_gain_loss": 62450.00,
    "total_gain_loss_pct": 16.15,
    "analytics": { "xirr": 0.185 },
    "holdings": [
        { "symbol": "RELIANCE.NS", "total_quantity": 50, "avg_price": 1350.00, "current_valuation": 71440.00, "gain_loss_pct": 5.84 },
        { "symbol": "120444", "total_quantity": 1500, "avg_price": 45.20, "current_valuation": 78345.00, "gain_loss_pct": 15.55 },
        { "symbol": "HDFCBANK.NS", "total_quantity": 100, "avg_price": 1620.00, "current_valuation": 175400.00, "gain_loss_pct": 8.27 },
        { "symbol": "118989", "total_quantity": 120, "avg_price": 450.00, "current_valuation": 62140.00, "gain_loss_pct": 15.07 }
    ],
    "ai_insights": {
        "RISK_INSIGHT": { "content": "Risk Alert: Reliance Industries and HDFC Top 100 make up 45% of your total equity exposure.", "importance": 9.5 },
        "PORTFOLIO_BRIEFING": { "content": "Nifty 50 momentum is stable; your portfolio is outperforming benchmark by 2.1%.", "importance": 8.0 }
    },
    "latest_news": {
        "RELIANCE.NS": [{ "title": "Reliance targets retail expansion in Q1", "url": "#", "sentiment": "POSITIVE" }],
        "120444": [{ "title": "Axis Bluechip NAV reflects large-cap stability", "url": "#", "sentiment": "NEUTRAL" }],
        "118989": [{ "title": "HDFC Top 100 reports quarterly AUM growth", "url": "#", "sentiment": "POSITIVE" }]
    },
    "rebalance_plan": {
        "drift_severity": "WARNING",
        "suggestions": [
            { "symbol": "RELIANCE.NS", "target_weight": 30.0, "current_weight": 37.0, "action": "SELL", "quantity": 9.4, "price": 2857.6 },
            { "symbol": "HDFCBANK.NS", "target_weight": 40.0, "current_weight": 42.8, "action": "BUY", "quantity": 12.2, "price": 1654.0 }
        ]
    },
    "fund_overlap": {
        "overlap_severity": "LOW",
        "total_overlap_score": 12.45,
        "effective_exposures": [
            { "symbol": "ICICIBANK", "total_weight": 8.20, "fund_count": 2 }
        ]
    }
};

function getMockData() {
    const localData = localStorage.getItem('finreview_demo_state');
    return localData ? JSON.parse(localData) : INITIAL_MOCK_DATA;
}

function saveMockData(data) {
    localStorage.setItem('finreview_demo_state', JSON.stringify(data));
}
