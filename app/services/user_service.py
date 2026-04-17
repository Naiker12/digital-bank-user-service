import json
import boto3
import os
import uuid
import hashlib
import time
import base64
import logging
from datetime import datetime, timezone, timedelta
from app.utils.dynamodb import table
from app.utils.s3 import s3, BUCKET
from app.utils.jwt import create_access_token
from app.utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)

sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'us-east-1'))
CARD_QUEUE_URL = os.getenv('CARD_QUEUE_URL')
NOTIFICATION_QUEUE_URL = os.getenv('NOTIFICATION_QUEUE_URL')

def register_user(body: dict):
    user_uuid = str(uuid.uuid4())
    password_hash = hash_password(body['password'])
    
    user_item = {
        'uuid': user_uuid,
        'document': str(body['document']),
        'name': body['name'],
        'lastName': body['lastName'],
        'email': body['email'],
        'password': password_hash,
        'address': body.get('address', ''),
        'phone': body.get('phone', ''),
        'avatarUrl': ''
    }
    
    table.put_item(Item=user_item)
    
    # Send messages to Card Queue (Debit and Credit)
    if CARD_QUEUE_URL:
        for card_type in ['DEBIT', 'CREDIT']:
            sqs.send_message(
                QueueUrl=CARD_QUEUE_URL,
                MessageBody=json.dumps({
                    'userId': user_uuid,
                    'request': card_type
                })
            )
            
    # Send Registration Notification
    if NOTIFICATION_QUEUE_URL:
        sqs.send_message(
            QueueUrl=NOTIFICATION_QUEUE_URL,
            MessageBody=json.dumps({
                'type': 'USER.REGISTER',
                'data': {
                    'userId': user_uuid,
                    'name': body['name'],
                    'document': body['document'],
                    'email': body['email']
                }
            })
        )
        
    return {'userId': user_uuid, 'message': 'User registered and cards requested'}

def login_user(email, password):
    # Scan is expensive, but used here as GSI is not yet confirmed
    response = table.scan()
    users = response.get('Items', [])
    db_user = next((u for u in users if u.get('email') == email), None)

    if not db_user or not verify_password(password, db_user.get('password')):
        return None  # Will be handled by wrapper as 401

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
                    "date": datetime.now(timezone.utc).isoformat()
                }
            })
        )

    return {
        'access_token': token,
        'token_type': 'bearer',
        'user_id': db_user.get('uuid'),
        'user': {
            'name': db_user.get('name'),
            'lastName': db_user.get('lastName'),
            'email': db_user.get('email')
        }
    }

def get_user_profile(user_id):
    # Using query by UUID
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('uuid').eq(user_id)
    )
    items = response.get('Items', [])
    if not items:
        return None
        
    user = items[0]
    if 'password' in user:
        del user['password']
    return user

def update_user_profile(user_id, data):
    # Need document for the composite key
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('uuid').eq(user_id)
    )
    items = response.get('Items', [])
    if not items:
        return None
        
    user_document = str(items[0]['document'])
    
    update_expr = "SET"
    attr_values = {}
    
    if 'address' in data:
        update_expr += " address = :a,"
        attr_values[':a'] = str(data['address'])
    if 'phone' in data:
        update_expr += " phone = :p,"
        attr_values[':p'] = str(data['phone'])

    if not attr_values:
        return {"message": "No fields to update"}

    update_expr = update_expr.rstrip(',')

    table.update_item(
        Key={'uuid': user_id, 'document': user_document},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=attr_values,
        ReturnValues="UPDATED_NEW"
    )
    return {"message": "Profile updated successfully"}

def upload_avatar(user_id, image_data, file_type='image/png'):
    file_extension = file_type.split('/')[-1]
    unique_name = f"{user_id}_{int(time.time())}"
    file_key = f"avatars/{unique_name}.{file_extension}"
    
    image_bytes = base64.b64decode(image_data)

    s3.put_object(
        Bucket=BUCKET,
        Key=file_key,
        Body=image_bytes,
        ContentType=file_type
    )

    avatar_url = f"https://{BUCKET}.s3.amazonaws.com/{file_key}"

    # Update user profile
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('uuid').eq(user_id)
    )
    if response.get('Items'):
        doc = response['Items'][0]['document']
        table.update_item(
            Key={'uuid': user_id, 'document': doc},
            UpdateExpression="SET avatarUrl = :val",
            ExpressionAttributeValues={':val': avatar_url}
        )

    return {'message': 'Avatar uploaded successfully', 'url': avatar_url}
