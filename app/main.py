"""
Main Mysafeip API pages
"""
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi import Depends, FastAPI, HTTPException, Request, Response, encoders, Form

from auth import authenticate,  create_access_token, get_current_user, check_user
import crud
import models
import schemas
from database import engine, get_db

#Init database and tables if not exists
models.Base.metadata.create_all(bind=engine)

#Init fastapi and disable docs without login
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.get("/docs")
async def get_documentation(current_user: models.User = Depends(get_current_user)):
    """Force authentication for doc page"""
    if current_user.is_admmin:
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
    raise HTTPException(status_code=401, detail="Only admins can use fastapi docs")

@app.get("/openapi.json")
async def openapi(current_user: models.User = Depends(get_current_user)):
    """Force authentication for openapi page"""
    if current_user.is_admmin:
        return get_openapi(title = "FastAPI", version="0.1.0", routes=app.routes)
    raise HTTPException(status_code=401, detail="Only admins can use openapi.json")
#Mount static directory files and jinja files
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pages definitions

@app.get("/")
async def main(request: Request, db: Session = Depends(get_db)):
    """Home page get request"""
    alert = {"success": "","danger": "","warning": ""}
    client_host = request.client.host
    user = await check_user(request, db)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert})

@app.get("/signin")
async def get_signin(request: Request, db: Session = Depends(get_db)):
    """Signin get request"""
    alert = {"success": "","danger": "","warning": ""}
    user = await check_user(request, db)
    return templates.TemplateResponse("signin.html", {"request": request, "user": user, "alert": alert})

@app.post("/signin")
def post_signin(
    response: Response,request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends() ):
    """Signin post request"""
    alert = {"success": "","danger": "","warning": ""}
    client_host = request.client.host
    user = authenticate(email=form_data.username, password=form_data.password, db=db)
    
    if not user:
        alert["warning"] = "Incorrect username or password"
        #raise HTTPException(status_code=400, detail="Incorrect username or password")  # 3
        response = templates.TemplateResponse(
        "signin.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert}) 
        return response

    access_token = create_access_token(sub=user.id)
    encoded_token = encoders.jsonable_encoder(access_token)
    
    for scope in form_data.scopes:
        if scope == "cli":
            return {
            "access_token": access_token
            }
    alert["success"] = "Signin success"
    response = templates.TemplateResponse(
        "home.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert})
    response.set_cookie(
    key="access_token",
    value=f"Bearer {encoded_token}",
    httponly=True)

    return response

@app.get("/logout")
def logout(response : Response,request: Request):
    """logout get request"""
    alert = {"success": "","danger": "","warning": ""}
    client_host = request.client.host
    user = ""
    #response = RedirectResponse('/signin', status_code= 302)

    alert["success"] = "Logout successfull"
    response = templates.TemplateResponse("home.html",
    {"request": request, "client_host": client_host, "user": user, "alert": alert})
    response.delete_cookie(key ='access_token')
  

    return response

@app.get("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    """register get request"""
    alert = {"success": "","danger": "","warning": ""}
    user = await check_user(request, db)
    return templates.TemplateResponse("register.html", {"request": request, "user": user, "alert": alert})

@app.post("/register")
def post_register(request: Request, email: str = Form(), password: str = Form(), confirm_password: str = Form(), db: Session = Depends(get_db)):
    """register post request"""
    alert = {"success": "","danger": "","warning": ""}

    db_user = crud.get_user_by_email(db, email)
    client_host = request.client.host
    user = ""
    if db_user:
        alert["warning"] = "Email already registered."
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert}) 
        return response
    if confirm_password != password:
        alert["warning"] = "Password missmatch!"
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert}) 
        return response
    
    if schemas.UserCreate(email=email, is_admin=False, password=password):
        alert["success"] = "Account creation successfull, you can now signin."
    else:
        alert["danger"] = "An error occured during your account creation."
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert}) 
        return response
    
    response = templates.TemplateResponse(
        "signin.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert})

    return response


@app.get("/get_users/", response_model=list[schemas.User])
def read_users(skip: int = 0,
limit: int = 100,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """read and return all users"""
    if current_user.is_admin:
        users = crud.get_users(db, skip=skip, limit=limit)
    else:
        raise HTTPException(status_code=401, detail="Only admins can search users")
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """search and return one user by id"""
    if current_user.is_admin:
        db_user = crud.get_user(db, user_id=user_id)
    else:
        raise HTTPException(status_code=401, detail="Only admins can search users")

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/post_ip/", response_model=schemas.Ip)
def create_ip_for_user(request: Request,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """declare one ip"""
    ip_value = request.client.host
    return crud.create_user_ip(db=db, ip=ip_value, user_id=current_user.id)


@app.get("/api/get_ips/", response_model=list[schemas.Ip])
def read_ips(skip: int = 0,
limit: int = 100,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """return all ips"""
    if current_user.is_admin:
        ips = crud.get_ips(db, skip=skip, limit=limit)
    else:
        ips = crud.get_ips(db, skip=skip, limit=limit)
    return ips
