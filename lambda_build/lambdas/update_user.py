import json
from app.services.user_service import update_user_profile

def handler(event, context):
    try:
        user_id = event.get('pathParameters', {}).get('user_id')
        body = json.loads(event.get('body', '{}'))

        if not user_id:
            return build_response(400, {'error': 'User ID is required'})

        result = update_user_profile(user_id, body)
        if not result:
            return build_response(404, {'error': 'User not found'})

        return build_response(200, result)
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
