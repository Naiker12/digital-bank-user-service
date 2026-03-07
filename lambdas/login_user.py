import json
import boto3
import os
from passlib.hash import bcrypt
from jose import jwt
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bank-users')

SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecuresecret')
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')

        if not email or not password:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing credentials'})
            }

        response = table.scan()
        users = response.get('Items', [])
        db_user = next((u for u in users if u['email'] == email), None)

        if not db_user or not bcrypt.verify(password, db_user['password']):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid email or password'})
            }

        token = create_access_token({
            "user_id": db_user["user_id"],
            "email": db_user["email"]
        })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'access_token': token,
                'token_type': 'bearer'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
