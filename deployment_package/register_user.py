import json
import boto3
import uuid
import os
from passlib.hash import pbkdf2_sha256

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('USERS_TABLE', 'bank-users'))
sqs = boto3.client('sqs')

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        user_uuid = str(uuid.uuid4())
        
        # Guardamos el documento como clave obligatoria (Sort Key)
        user_item = {
            'uuid': user_uuid,
            'document': str(body['document']),
            'name': body['name'],
            'lastName': body['lastName'],
            'email': body['email'],
            'password': pbkdf2_sha256.hash(body['password']),
            'status': 'ACTIVE',
            'createdAt': str(uuid.uuid1()) # Timestamp o ID único para orden
        }
        
        table.put_item(Item=user_item)
        
        # Enviamos a la cola para crear tarjetas (Card Service)
        sqs.send_message(
            QueueUrl=os.getenv('CARD_QUEUE_URL'),
            MessageBody=json.dumps({
                'userId': user_uuid, 
                'email': body['email'],
                'name': body['name'],
                'lastName': body['lastName']
            })
        )
        
        return {
            'statusCode': 201,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'User registered successfully', 
                'user_id': user_uuid,
                'document': body['document']
            })
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
