import json
from services.portfolio_service import PortfolioService

portfolio_service = PortfolioService()

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id', 'test_user') # For MVP
        symbol = body.get('symbol')
        tx_type = body.get('type', 'BUY')
        quantity = body.get('quantity')
        price = body.get('price')

        if not symbol or not quantity or not price:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Missing required fields'})
            }

        result = portfolio_service.add_transaction(user_id, symbol, tx_type, quantity, price)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Holding recorded', 'data': result})
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }
