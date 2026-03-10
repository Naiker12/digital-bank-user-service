import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('USERS_TABLE', 'bank-users'))

def handler(event, context):
    try:
        user_id = event.get('pathParameters', {}).get('user_id')
        
        # 1. Fetch user by UUID using Query
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('uuid').eq(user_id)
        )
        
        items = response.get('Items', [])
        
        if not items:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'User not found'})
            }
            
        user = items[0]
        # 2. Remove password from response for security
        if 'password' in user:
            del user['password']
            
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(user)
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }
