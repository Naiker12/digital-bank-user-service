import json
import boto3
import os
import base64
import time
import uuid

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('USERS_TABLE', 'bank-users'))
bucket_name = os.getenv('S3_BUCKET')

def handler(event, context):
    try:
        user_id = event.get('pathParameters', {}).get('user_id')
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('image')
        file_type = body.get('fileType', 'image/png')

        if not image_data:
            return build_response(400, {'error': 'No image data provided'})

        # 🖼️ Generar nombre único para evitar duplicados (Requerimiento de diseño)
        file_extension = file_type.split('/')[-1]
        unique_name = f"{user_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        file_name = f"avatars/{unique_name}.{file_extension}"
        
        image_bytes = base64.b64decode(image_data)

        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=image_bytes,
            ContentType=file_type
        )

        avatar_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"

        # 🔍 Recuperar SK (document) para actualizar perfil
        user_response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('uuid').eq(user_id)
        )
        
        if user_response.get('Items'):
            doc = user_response['Items'][0]['document']
            table.update_item(
                Key={'uuid': user_id, 'document': doc},
                UpdateExpression="SET avatarUrl = :val",
                ExpressionAttributeValues={':val': avatar_url}
            )

        return build_response(200, {'message': 'Avatar uploaded successfully', 'url': avatar_url})

    except Exception as e:
        print(f"Error fatal en upload_avatar: {str(e)}")
        return build_response(500, {'error': str(e)})

def build_response(status, body_data):
    return {
        'statusCode': status,
        'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
        'body': json.dumps(body_data)
    }
