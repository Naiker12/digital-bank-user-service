import json
from app.services.user_service import login_user

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')

        if not email or not password:
            return build_response(400, {'error': 'Email and password are required'})

        result = login_user(email, password)
        if not result:
            return build_response(401, {'error': 'Invalid credentials'})

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
