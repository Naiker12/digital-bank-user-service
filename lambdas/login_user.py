import json
import boto3
import os
import datetime
import hashlib
from jose import jwt

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('USERS_TABLE', 'bank-users'))
sqs = boto3.client('sqs')

SECRET_KEY = os.getenv('JWT_SECRET', 'super-secret-bank-key-2026')
ALGORITHM = "HS256"
NOTIFICATION_QUEUE_URL = os.getenv('NOTIFICATION_QUEUE_URL', '')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')

        if not email or not password:
            return build_response(400, {'error': 'Email and password are required'})

        # Hash the incoming password to compare
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Simple scan to find user by email (For production use a GSI)
        response = table.scan()
        users = response.get('Items', [])
        db_user = next((u for u in users if u.get('email') == email), None)

        if not db_user or db_user.get('password') != password_hash:
            return build_response(401, {'error': 'Invalid credentials'})

        token = create_access_token({
            "user_id": db_user.get("uuid"),
            "email": db_user.get("email")
        })

        # Notificación de Login
        if NOTIFICATION_QUEUE_URL:
            sqs.send_message(
                QueueUrl=NOTIFICATION_QUEUE_URL,
                MessageBody=json.dumps({
                    "type": "USER.LOGIN",
                    "data": {
                        "userId": db_user.get("uuid"),
                        "email": email,
                        "date": datetime.datetime.utcnow().isoformat()
                    }
                })
            )

        return build_response(200, {
            'access_token': token,
            'token_type': 'bearer',
            'user_id': db_user.get('uuid')
        })

    except Exception as e:
        return build_response(500, {'error': str(e)})

def build_response(status, body):
    return {
        'statusCode': status,
        'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }
