from sqlalchemy.orm import Session
import security
from schemas import UserCreate, IpCreate
from models import User, Ip

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session):
    return db.query(User).all()


def create_user(db: Session, user: UserCreate):
    db_user = User(
        email=user.email,
        is_admin=user.is_admin,
        hashed_password=security.get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, email):
    db_user = get_user_by_email(db, email)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True

def get_ips(db: Session, user):
    if user.is_admin:
        return db.query(Ip).all()
    else:
        return db.query(Ip).filter(Ip.owner == user)

def get_ip(db: Session, ip_id: int):
    return db.query(Ip).get(ip_id)

def delete_ip(db: Session, id):
    print(id)
    db_ip = get_ip(db, id)
    print(db_ip)
    if not db_ip:
        return False
    db.delete(db_ip)
    db.commit()
    return True

def create_user_ip(db: Session, ip: IpCreate, user_id: int):
    db_ip = Ip(description="test", value=ip, owner_id=user_id)
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip
    