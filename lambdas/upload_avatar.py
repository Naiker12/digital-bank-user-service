import json
from app.services.user_service import upload_avatar

def handler(event, context):
    try:
        user_id = event.get('pathParameters', {}).get('user_id')
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('image')
        file_type = body.get('fileType', 'image/png')

        if not user_id or not image_data:
            return build_response(400, {'error': 'User ID and image data are required'})

        result = upload_avatar(user_id, image_data, file_type)
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
