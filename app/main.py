"""
Main Mysafeip API pages
"""
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse

from fastapi import Depends, FastAPI, HTTPException, Request, Response, encoders, Form, status

from auth import authenticate, create_access_token, get_current_user, check_user
import crud
import models
import schemas
from settings import settings
from database import engine, get_db
from routers import users, ips

#Init database and tables if not exists
models.Base.metadata.create_all(bind=engine)

#Init fastapi and disable docs without login
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#Include routers
app.include_router(users.router)
app.include_router(ips.router)


#Mount static directory files and jinja files
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

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
    response: Response,
    request: Request,
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
        "signin.html",
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

    if settings.DISABLE_REGISTER:
        alert["warning"] = "Register is not allowed"

    user = await check_user(request, db)
    return templates.TemplateResponse("register.html", {"request": request, "user": user, "alert": alert})

@app.post("/register")
async def post_register(request: Request, email: str = Form(), password: str = Form(), confirm_password: str = Form(), db: Session = Depends(get_db)):
    """register post request"""
    client_host = request.client.host
    alert = {"success": "","danger": "","warning": ""}
    user = await check_user(request, db)
    if settings.DISABLE_REGISTER:
        alert["danger"] = "Register is not allowed"
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert}) 
        return response


    if user:
        alert["warning"] = "You are already logged"
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert}) 
        return response

    db_user = crud.get_user_by_email(db, email)

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

    new_user = schemas.UserCreate(email=email, is_admin=False, password=password)
    user = crud.create_user(db=db, user=new_user)
    if user:
        alert["success"] = "Account creation successfull."
    else:
        alert["danger"] = "An error occured during your account creation."
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert}) 
        return response
    
    access_token = create_access_token(sub=user.id)
    encoded_token = encoders.jsonable_encoder(access_token)

    response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert})

    response.set_cookie(
    key="access_token",
    value=f"Bearer {encoded_token}",
    httponly=True)

    return response
    #return RedirectResponse("/signin", status_code=status.HTTP_303_SEE_OTHER)    
