from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel, EmailStr
from app.services import user_service

router = APIRouter()

class UserRegister(BaseModel):
    document: str
    name: str
    lastName: str
    email: EmailStr
    password: str
    address: str = ""
    phone: str = ""

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    address: str = None
    phone: str = None

@router.post("/register", status_code=201)
async def register(user: UserRegister):
    try:
        return user_service.register_user(user.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(user: UserLogin):
    result = user_service.login_user(user.email, user.password)
    if not result:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return result

@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    user = user_service.get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.put("/profile/{user_id}")
async def update_profile(user_id: str, data: UserUpdate):
    result = user_service.update_user_profile(user_id, data.dict(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return result
