import sys
import crud
from database import SessionLocal
from schemas import UserCreate

def create_user(email, password, db):
    user = UserCreate(email=email, is_admin=True, is_active=True, password=password)
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise Exception("Email already registered")
    return crud.create_user(db, user)

db = SessionLocal()
try:
    create_user (email=sys.argv[1], password=sys.argv[2], db=db)
except:
    raise Exception("Usage: python init_admin.py yourmail@example.com your_password")
finally:
    db.close()
