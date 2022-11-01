from sqlalchemy.orm import Session
import security
from schemas import UserCreate, IpCreate
from models import User, Ip

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate):
    db_user = User(
        email=user.email,
        is_admin=user.is_admin,
        hashed_password=security.get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user.email

def get_ips(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Ip).offset(skip).limit(limit).all()

def create_user_ip(db: Session, ip: IpCreate, user_id: int):
    db_ip = Ip(description="test", value=ip, owner_id=user_id)
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip
    