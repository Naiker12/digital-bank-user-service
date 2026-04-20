import bcrypt
import hashlib

def _prepare_password(password: str) -> bytes:
    """
    Hashes the password with SHA-256 and returns the hex digest as bytes.
    This ensures the input to bcrypt never exceeds its internal limit (72 bytes).
    """
    pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pw_hash.encode('utf-8')

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    """
    prepared_pw = _prepare_password(password)
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared_pw, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against its bcrypt hash.
    """
    try:
        prepared_pw = _prepare_password(plain_password)
        return bcrypt.checkpw(prepared_pw, hashed_password.encode('utf-8'))
    except Exception:
        return False
