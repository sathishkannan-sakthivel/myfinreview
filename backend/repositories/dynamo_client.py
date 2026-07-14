import os
import boto3
from config import settings

class DynamoClient:
    def __init__(self):
        self.table_name = settings.TABLE_NAME
        self.region = settings.AWS_REGION
        self.endpoint_url = settings.DYNAMODB_ENDPOINT
        
        if self.endpoint_url:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region, endpoint_url=self.endpoint_url)
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            
        self.table = self.dynamodb.Table(self.table_name)

    def get_item(self, pk, sk):
        response = self.table.get_item(Key={'PK': pk, 'SK': sk})
        return response.get('Item')

    def put_item(self, item):
        return self.table.put_item(Item=item)

    def query_items(self, pk, sk_prefix=None):
        if sk_prefix:
            from boto3.dynamodb.conditions import Key
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(pk) & Key('SK').begins_with(sk_prefix)
            )
        else:
            from boto3.dynamodb.conditions import Key
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(pk)
            )
        return response.get('Items', [])

    def delete_item(self, pk, sk):
        return self.table.delete_item(Key={'PK': pk, 'SK': sk})
