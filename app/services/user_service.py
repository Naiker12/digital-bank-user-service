from app.utils.dynamodb import table
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token
import uuid

def register_user(user):
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user.password)

    item = {
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "password": hashed_password
    }

    table.put_item(Item=item)

    return {
        "message": "Usuario creado",
        "user_id": user_id
    }

def login_user(user):
    # Nota: scan() es costoso en producción, se optimizará luego con GSI por email
    response = table.scan()
    users = response.get("Items", [])

    db_user = next((u for u in users if u["email"] == user.email), None)

    if not db_user:
        return {"error": "Usuario no encontrado"}

    if not verify_password(user.password, db_user["password"]):
        return {"error": "Credenciales inválidas"}

    token = create_access_token({
        "user_id": db_user["user_id"],
        "email": db_user["email"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

def get_user_profile(user_id):
    response = table.get_item(
        Key={"user_id": user_id}
    )
    return response.get("Item")

def upload_avatar(user_id, file):
    from app.utils.s3 import s3, BUCKET
    import uuid

    file_key = f"avatars/{user_id}-{uuid.uuid4()}.png"

    s3.upload_fileobj(
        file.file,
        BUCKET,
        file_key
    )

    avatar_url = f"https://{BUCKET}.s3.amazonaws.com/{file_key}"

    table.update_item(
        Key={"user_id": user_id},
        UpdateExpression="set avatar = :a",
        ExpressionAttributeValues={
            ":a": avatar_url
        }
    )

    return {"avatar_url": avatar_url}

def list_users():
    response = table.scan()
    return response.get("Items", [])
