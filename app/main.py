from fastapi import Depends, FastAPI, HTTPException, Request, status, APIRouter
from sqlalchemy.orm import Session

import crud, models, schemas
from database import SessionLocal, engine
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from settings import settings
from pydantic import BaseModel
from typing import Optional
from jose import jwt, JWTError
from auth import authenticate,  create_access_token

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
#app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
router = APIRouter()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TokenData(BaseModel):
    username: Optional[str] = None

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
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

    user = db.query(models.User).filter(models.User.id == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


@app.post("/post_user/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db),current_user: models.User = Depends(get_current_user)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="Only Admins are authoriezd to create users")
    return crud.create_user(db=db, user=user)


@app.get("/get_users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


#@app.get("/users/{user_id}", response_model=schemas.User)
#def read_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
#    db_user = crud.get_user(db, user_id=user_id)
#    if db_user is None:
#        raise HTTPException(status_code=404, detail="User not found")
#    return db_user

@app.post("/post_ip/", response_model=schemas.Ip)
def create_ip_for_user(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ip_value = request.client.host
    return crud.create_user_ip(db=db, ip=ip_value, user_id=current_user.id)

@app.get("/get_ips/", response_model=list[schemas.Ip])
def read_ips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ips = crud.get_ips(db, skip=skip, limit=limit)
    return ips

@app.get("/")
async def main(request: Request):
   client_host = request.client.host
   return {"Message":"Welcome " + client_host}

@app.post("/api/v1/auth/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends() ):
    """
    Get the JWT for a user with data from OAuth2 request form body.
    """

    user = authenticate(email=form_data.username, password=form_data.password, db=db)  # 2
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")  # 3

    return {
        "access_token": create_access_token(sub=user.id),  # 4
        "token_type": "bearer",
    }