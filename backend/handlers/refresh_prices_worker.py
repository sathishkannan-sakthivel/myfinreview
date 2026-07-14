import json
from services.price_service import PriceService

price_service = PriceService()

def lambda_handler(event, context):
    try:
        for record in event['Records']:
            body = json.loads(record['body'])
            symbols = body.get('symbols', [])
            
            print(f"Refreshing prices for: {symbols}")
            price_service.refresh_prices(symbols)
            
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Prices refreshed'})
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }
