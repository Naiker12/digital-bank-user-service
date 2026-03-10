import json
import boto3
import os
import uuid
import hashlib

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
table = dynamodb.Table(os.getenv('USERS_TABLE', 'bank-users'))
queue_url = os.getenv('CARD_QUEUE_URL')
notification_queue_url = os.getenv('NOTIFICATION_QUEUE_URL')

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        user_uuid = str(uuid.uuid4())
        
        # 1. Password Encryption
        password_hash = hashlib.sha256(body['password'].encode()).hexdigest()
        
        user_item = {
            'uuid': user_uuid,
            'document': str(body['document']),
            'name': body['name'],
            'lastName': body['lastName'],
            'email': body['email'],
            'password': password_hash,
            'address': '',
            'phone': '',
            'avatarUrl': ''
        }
        
        table.put_item(Item=user_item)
        
        # 2. Request Debit Card
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                'userId': user_uuid,
                'request': 'DEBIT'
            })
        )
        
        # 3. Request Credit Card
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                'userId': user_uuid,
                'request': 'CREDIT'
            })
        )

        # 4. Welcome Notification
        if notification_queue_url:
            sqs.send_message(
                QueueUrl=notification_queue_url,
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

        return build_response(201, {'userId': user_uuid, 'message': 'User registered and cards requested'})

    except Exception as e:
        return build_response(500, {'error': str(e)})

def build_response(status, body):
    return {
        'statusCode': status,
        'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }
