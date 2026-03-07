from fastapi import APIRouter, Depends, UploadFile, File
from app.models.user_model import UserCreate, UserLogin
from app.services.user_service import register_user, login_user, get_user_profile, upload_avatar
from app.utils.auth import verify_token

router = APIRouter()

@router.post("/register")
def register(user: UserCreate):
    return register_user(user)

@router.post("/login")
def login(user: UserLogin):
    return login_user(user)

@router.get("/protected")
def protected_route(user=Depends(verify_token)):
    return {
        "message": "Access granted",
        "user": user
    }

@router.get("/profile")
def profile(user=Depends(verify_token)):
    user_id = user["user_id"]
    profile = get_user_profile(user_id)
    return profile

@router.post("/avatar")
def upload_avatar_route(
    file: UploadFile = File(...),
    user=Depends(verify_token)
):
    user_id = user["user_id"]
    return upload_avatar(user_id, file)

@router.get("/all")
def get_users():
    from app.services.user_service import list_users
    return list_users()
