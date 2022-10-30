from fastapi.responses import RedirectResponse
from fastapi import Depends, FastAPI, HTTPException, Request, Response, encoders, Form
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import crud, models, schemas
from database import engine
from fastapi.security import OAuth2PasswordRequestForm
from auth import authenticate,  create_access_token, get_current_user, check_user
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from database import get_db

#Init database and tables if not exists
models.Base.metadata.create_all(bind=engine)

#Init fastapi and disable docs without login
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
@app.get("/docs")
async def get_documentation(current_user: models.User = Depends(get_current_user)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
@app.get("/openapi.json")
async def openapi(current_user: models.User = Depends(get_current_user)):
    return get_openapi(title = "FastAPI", version="0.1.0", routes=app.routes)

#Mount static directory files and jinja files
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pages definitions

@app.get("/")
async def main(request: Request, db: Session = Depends(get_db)):
    client_host = request.client.host
    user = await check_user(request, db)
    return templates.TemplateResponse("home.html", {"request": request, "client_host": client_host, "user": user})

@app.get("/signin")
async def main(request: Request):
   return templates.TemplateResponse("signin.html", {"request": request})

@app.post("/signin")
def login(response: Response,request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends() ):
    """
    Get the JWT for a user with data from OAuth2 request form body.
    """
    response = templates.TemplateResponse("signin.html", {"request": request})
    user = authenticate(email=form_data.username, password=form_data.password, db=db)  # 2
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")  # 3
    access_token = create_access_token(sub=user.id)
    response.set_cookie(
        key="access_token", value="{}".format(encoders.jsonable_encoder(access_token)), httponly=True
        #key="access_token", value="Bearer {}".format(encoders.jsonable_encoder(access_token)), httponly=True

    )
    for scope in form_data.scopes:
        if scope == "cli":
            return {
            "access_token": access_token
            }
    return response

@app.get("/logout")
def logout(response : Response):
  response = RedirectResponse('/signin', status_code= 302)
  response.delete_cookie(key ='access_token')
  return response

@app.get("/register")
async def main(request: Request):
   return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def create_user(email: str = Form(), password: str = Form(), db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        user = schemas.UserCreate(email=email, is_admin=False, password=password)
    return crud.create_user(db=db, user=user)


@app.get("/get_users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/post_ip/", response_model=schemas.Ip)
def create_ip_for_user(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ip_value = request.client.host
    return crud.create_user_ip(db=db, ip=ip_value, user_id=current_user.id)


@app.get("/api/get_ips/", response_model=list[schemas.Ip])
def read_ips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ips = crud.get_ips(db, skip=skip, limit=limit)
    return ips