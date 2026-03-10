import json
import boto3
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('USERS_TABLE', 'bank-users'))

def handler(event, context):
    try:
        user_id = event.get('pathParameters', {}).get('user_id')
        if not user_id:
            return build_response(400, {'error': 'User ID is missing in path'})

        body = json.loads(event.get('body', '{}'))
        address = body.get('address')
        phone = body.get('phone')

        # 1. Get user document (Sort Key)
        response = table.query(
            KeyConditionExpression=Key('uuid').eq(user_id)
        )
        
        items = response.get('Items', [])
        if not items:
            return build_response(404, {'error': f'User {user_id} not found'})
            
        user_document = str(items[0]['document'])

        # 2. Prepare update
        if not address and not phone:
            return build_response(400, {'error': 'No fields provided for update (address or phone)'})

        update_expr = "SET"
        attr_values = {}
        
        if address:
            update_expr += " address = :a,"
            attr_values[':a'] = str(address)
        if phone:
            update_expr += " phone = :p,"
            attr_values[':p'] = str(phone)

        update_expr = update_expr.rstrip(',')

        # 3. Execute update
        table.update_item(
            Key={
                'uuid': str(user_id),
                'document': user_document
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=attr_values,
            ReturnValues="UPDATED_NEW"
        )
        
        return build_response(200, {'message': 'Profile updated successfully'})

    except Exception as e:
        print(f"Error updating user: {str(e)}")
        return build_response(500, {'error': str(e)})

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
