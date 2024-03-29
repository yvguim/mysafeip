import secrets
from sqlalchemy.orm import Session
import security
from schemas import UserCreate, IpCreate, InstantAccessCreate, TokenCreate
from models import User, Ip, InstantAccess, Token
import pyotp
from settings import settings

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

def reset_user_password(db: Session, user: User, password: str):
    user = db.query(User).get(user.id)
    user.hashed_password=security.get_password_hash(password)
    db.commit()
    db.refresh(user)
    return user

def enable_user_twofactor(db: Session, user: User):
    user = db.query(User).get(user.id)
    user.twofactor = pyotp.random_base32()
    db.commit()
    db.refresh(user)
    return user

def disable_user_twofactor(db: Session, user: User):
    user = db.query(User).get(user.id)
    user.twofactor = ""
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, email):
    db_user = get_user_by_email(db, email)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True

def get_ips(db: Session, user):
    if user.is_admin and settings.ADMIN_SEE_USERS_IP:
        return db.query(Ip).all()
    else:
        return db.query(Ip).filter(Ip.owner == user)

def get_ip(db: Session, ip_id: int):
    return db.query(Ip).get(ip_id)

def delete_ip(db: Session, id):
    db_ip = get_ip(db, id)
    if not db_ip:
        return False
    db.delete(db_ip)
    db.commit()
    return True

def get_ip_for_user(db: Session, user_id: int, ip, origin, description):
    return db.query(Ip).filter(Ip.owner_id == user_id, Ip.value == ip.strip(), Ip.origin == origin, Ip.description == description).first()

def create_user_ip(db: Session, user_id: int, ip, origin = "", description = ""):
    ip_exists = get_ip_for_user(db, user_id = user_id, ip = ip, origin = origin, description = description)
    if not ip_exists:
        ip = IpCreate(description=description, value=ip, origin=origin, owner_id=user_id)
        ip_data = ip.dict()
        db_ip = Ip(description=ip_data['description'], value=str(ip_data['value']), origin=str(ip_data['origin']), owner_id=ip_data['owner_id'])
        db.add(db_ip)
        db.commit()
        db.refresh(db_ip)
        return db_ip
    return ip_exists
    
def create_instant_access(db: Session, link: str, user_id: int, description = ""):
    unique_link = secrets.token_hex(16)
    ia = InstantAccessCreate(link=link, unique_link=unique_link, owner_id=user_id, description=description)
    ia_data = ia.dict()
    db_ia = InstantAccess(description=ia_data['description'], link=str(ia_data['link']), unique_link=ia_data['unique_link'], owner_id=ia_data['owner_id'])
    db.add(db_ia)
    db.commit()
    db.refresh(db_ia)
    return db_ia

def create_new_token(db, user_id: int, description: None):
    key = secrets.token_hex(16)
    secret = secrets.token_hex(32)
    token = TokenCreate(key=key, secret=secret, owner_id=user_id, description=description)
    token_data = token.dict()
    db_token = Token(description=token_data['description'], key=str(token_data['key']), secret=security.get_password_hash(token_data['secret']), owner_id=token_data['owner_id'])
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return {"key": db_token.key, "secret": secret}

def get_tokens(db: Session, user):
        return db.query(Token).filter(Token.owner == user)

def get_token(db: Session, id):
    return db.query(Token).get(id)

def delete_token(db: Session, id):
    db_token = get_token(db, id)
    if not db_token:
        return False
    db.delete(db_token)
    db.commit()
    return True
    
def get_link(db: Session, link_id: int):
    return db.query(InstantAccess).get(link_id)

def get_links(db: Session, user):
    return db.query(InstantAccess).filter(InstantAccess.owner == user)

def get_link_by_unique_link(db: Session, unique_link: str):
    return db.query(InstantAccess).filter(InstantAccess.unique_link == unique_link).first()

def delete_link(db: Session, id):
    db_link = get_link(db, id)
    if not db_link:
        return False
    origin = db_link.unique_link
    ips_to_delete = db.query(Ip).filter(Ip.origin == origin).all()
    for ip in ips_to_delete:
        delete_ip(db, ip.id)
    db.delete(db_link)
    db.commit()
    return True