from typing import Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm.session import Session
from jose import jwt, JWTError
from models import User, Token
from schemas import TokenData
from settings import settings
from security import verify_password
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi import Request, HTTPException, status, Depends
from fastapi.security.utils import get_authorization_scheme_param
from database import get_db
import re
import glob
import os
import json


# Redefine OAuth2PasswordBearer to add cookie support (for browser)
class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        #If client got an access_token cookie, try to use it  as authentication
        if request.cookies.get("access_token"):
            authorization: str = request.cookies.get("access_token")
        else:
            authorization: str = request.headers.get("Authorization") 

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            else:
                return None
        return param
    
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=f"/signin")
    
def password_validity(password: str):
    if (len(password) < 6):
        return False
    elif not re.search("[a-z]" , password):
        return False
    elif not re.search("[A-Z]" , password):
        return False
    elif not re.search("[0-9]" , password):
        return False
    elif not re.search("[ !\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]" , password):
        return False
    return True
    
    
def authenticate(
    *,
    email: str,
    password: str,
    db: Session,
) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):  # 1
        return None
    return user

def authenticate_by_key(
    key: str,
    secret: str,
    db: Session,
) -> Optional[User]:
    token = db.query(Token).filter(Token.key == key).first()
    if not token:
        return None
    if not verify_password(secret, token.secret): 
        return None

    return token.owner

def create_access_token(*, sub: str) -> str:  # 2
    return _create_token(
        token_type="access_token",
        lifetime=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),  # 3
        sub=sub,
    )


def _create_token(
    token_type: str,
    lifetime: timedelta,
    sub: str,
) -> str:
    payload = {}
    expire = datetime.utcnow() + lifetime
    payload["type"] = token_type
    payload["exp"] = expire  # 4
    payload["iat"] = datetime.utcnow()  # 5
    payload["sub"] = str(sub)  # 6

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        #status_code=status.HTTP_401_UNAUTHORIZED,
        #detail="Could not validate credentials",
        #headers={"WWW-Authenticate": "Bearer"},
        status_code=302,
        detail="Could not validate credentials",
        headers = {"Location": "/logout", "Set-Cookie": "access_token=deleted"} 
    )
    try:
        payload = jwt.decode(
            token.replace('Bearer ', ''),
            settings.JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        #return False

    user = db.query(User).filter(User.id == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def check_user(request: Request, db):
    token = request.cookies.get("access_token")
    current_user = ""
    if token:
        current_user: User = await get_current_user(token=token, db=db)
    return current_user

def check_user_language(request: Request, lang = None):
    languages = {}
    language_list = glob.glob("languages/*.json")
    for language in language_list:
        filename  = os.path.basename(language)
        lang_code, ext = os.path.splitext(filename)
        with open(language, 'r', encoding='utf8') as file:
            languages[lang_code] = json.load(file)
    
    print(lang)
        
    lang = lang or request.cookies.get("lang")
    if lang and lang in ['en', 'fr']:
        return languages[lang]
    return languages["en"]
