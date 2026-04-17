import json
from app.services.user_service import register_user

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        result = register_user(body)
        return build_response(201, result)
    except Exception as e:
        return build_response(500, {'error': str(e)})

def build_response(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
