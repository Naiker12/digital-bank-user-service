import json
import boto3
import os
import datetime
from passlib.hash import pbkdf2_sha256
from jose import jwt

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('USERS_TABLE', 'user-table'))
sqs = boto3.client('sqs')

SECRET_KEY = os.getenv('JWT_SECRET', 'supersecretkey')
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
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing credentials'})
            }

        # Disclaimer: Scanning is not recommended for production. Best practice is GSI over email.
        response = table.scan()
        users = response.get('Items', [])
        db_user = next((u for u in users if u.get('email') == email), None)

        if not db_user or not pbkdf2_sha256.verify(password, db_user.get('password', '')):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid email or password'})
            }

        token = create_access_token({
            "user_id": db_user.get("uuid"),
            "email": db_user.get("email")
        })

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
