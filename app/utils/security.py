from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import hashlib

def _prepare_password(password: str) -> str:
    # Use SHA-256 to hash the password into a 64-character hex string.
    # This prevents bcrypt's 71-byte limit error entirely.
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def hash_password(password: str):
    return pwd_context.hash(_prepare_password(password))

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(_prepare_password(plain_password), hashed_password)
