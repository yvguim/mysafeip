"""
Passwords functions
"""
from passlib.context import CryptContext


PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """return true if password match hashed argument"""
    return PWD_CONTEXT.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """hash a plain text string"""
    return PWD_CONTEXT.hash(password)
