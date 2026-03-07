import json
import boto3
import os
from jose import jwt

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bank-users')

SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecuresecret')
ALGORITHM = "HS256"

def handler(event, context):
    try:
        auth_header = event.get('headers', {}).get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }

        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('user_id')

        if not user_id:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid token'})
            }

        response = table.get_item(Key={'user_id': user_id})
        user = response.get('Item')

        if not user:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'User not found'})
            }

        # Don't return password in profile
        if 'password' in user:
            del user['password']

        return {
            'statusCode': 200,
            'body': json.dumps(user)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
