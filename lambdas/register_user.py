import json
import boto3
import uuid
import os
from passlib.hash import bcrypt

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bank-users')

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        email = body.get('email')
        password = body.get('password')

        if not name or not email or not password:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        user_id = str(uuid.uuid4())
        hashed_password = bcrypt.hash(password)

        item = {
            'user_id': user_id,
            'name': name,
            'email': email,
            'password': hashed_password
        }

        table.put_item(Item=item)

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'User created',
                'user_id': user_id
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
