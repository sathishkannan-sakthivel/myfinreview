import sys
import os
import json
from datetime import datetime
from unittest.mock import MagicMock

# Add backend to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_dir = os.path.join(project_root, 'backend')
sys.path.append(backend_dir)

# Mock Environment Variables BEFORE any imports
os.environ['TABLE_NAME'] = 'FinReviewTable'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['OPENROUTER_API_KEY'] = 'YOUR_OPENROUTER_KEY'
os.environ['MARKET_DATA_API_KEY'] = 'MOCK_KEY'
os.environ['MFAPI_BASE_URL'] = 'https://api.mfapi.in/mf/'

# --- IN-MEMORY MOCK DYNAMODB ---
class MockDynamoData:
    def __init__(self):
        self.store = {}

    def get(self, pk, sk):
        return self.store.get((pk, sk))

    def put(self, item):
        pk, sk = item['PK'], item['SK']
        self.store[(pk, sk)] = item
        return {}

    def query(self, pk, sk_prefix=""):
        results = []
        for (k_pk, k_sk), item in self.store.items():
            if k_pk == pk and k_sk.startswith(sk_prefix):
                results.append(item)
        results.sort(key=lambda x: x['SK'])
        return results

MOCK_DB = MockDynamoData()

# Monkeypatch DynamoClient
from repositories.dynamo_client import DynamoClient
print("Applying FinReview v1.0 Intelligence Mocks (with Indian Market Support)...")
DynamoClient.get_item = lambda self, pk, sk: MOCK_DB.get(pk, sk)
DynamoClient.put_item = lambda self, item: MOCK_DB.put(item)
DynamoClient.query_items = lambda self, pk, sk_prefix=None: MOCK_DB.query(pk, sk_prefix or "")
DynamoClient.delete_item = lambda self, pk, sk: MOCK_DB.store.pop((pk, sk), None)

def run_handler_check(name, handler_module, event):
    print(f"\n[Handler] Testing {name}...")
    try:
        from importlib import import_module
        if f"handlers.{handler_module}" in sys.modules:
            del sys.modules[f"handlers.{handler_module}"]
        
        module = import_module(f"handlers.{handler_module}")
        response = module.lambda_handler(event, {})
        print(f"Result: {response['statusCode']}")
        print(json.dumps(json.loads(response['body']), indent=2))
        return response
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🧞 FinReview v1.0 Indian Market Logic Verifier")
    
    # 1. Transactions - Indian Stock (NSE: RELIANCE)
    run_handler_check("Record Buy (Stock)", "record_transaction_handler", {
        "body": json.dumps({"user_id": "ind_user", "symbol": "RELIANCE.NS", "type": "BUY", "quantity": 10, "price": 2500.0})
    })

    # 2. Transactions - Indian Mutual Fund (AMFI: 120444 - Axis Bluechip Fund)
    print("\n[Action] Recording Mutual Fund transaction (Scheme Code: 120444)...")
    run_handler_check("Record Buy (MF)", "record_transaction_handler", {
        "body": json.dumps({"user_id": "ind_user", "symbol": "120444", "type": "BUY", "quantity": 100, "price": 50.0})
    })

    # 3. Analytics Core (XIRR + Concentration)
    run_handler_check("Compute Analytics", "analytics_calculator", {"user_id": "ind_user", "analytics_version": 1})

    # 4. Risk Alerts
    run_handler_check("Evaluate Alerts", "alerts_evaluator", {"user_id": "ind_user", "required_analytics_version": 1})

    # 5. Rebalancing Engine
    run_handler_check("Generate Rebalance Plan", "generate_rebalance_suggestions", {
        "user_id": "ind_user",
        "targets": [
            {"symbol": "RELIANCE.NS", "target_weight": 40.0}, 
            {"symbol": "HDFCBANK.NS", "target_weight": 30.0},
            {"symbol": "120444", "target_weight": 30.0}
        ]
    })

    # 6. News Module
    run_handler_check("Ingest News", "news_ingest_worker", {"user_id": "ind_user"})

    # 7. MF Overlap Detection
    # Using '120444' consistently to match the transaction recorded earlier
    print("\nAdding mock Mutual Fund holding for look-through analysis...")
    MOCK_DB.put({
        'PK': 'USER#ind_user', 'SK': 'HOLDING#120444',
        'symbol': '120444', 'total_quantity': 100, 'avg_price': 50.0, 'current_valuation': 5000.0
    })
    run_handler_check("Detect MF Overlap", "detect_fund_overlap", {"user_id": "ind_user"})

    # 8. AI Insights Pipeline
    run_handler_check("Update History", "analytics_calculator", {"user_id": "ind_user", "analytics_version": 2})
    run_handler_check("Generate AI Insights", "generate_insights_worker", {"user_id": "ind_user", "required_analytics_version": 2})

    # 9. Unified Summary API
    run_handler_check("Fetch Dashboard Data", "get_portfolio_summary_handler", {
        "queryStringParameters": {"user_id": "ind_user"}
    })
    
    print("\n--- FinReview v1.0 Indian Market Verification Complete! ---")
