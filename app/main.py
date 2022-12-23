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

from auth import authenticate, authenticate_by_key, create_access_token, get_current_user, check_user, check_user_language, password_validity
import crud
import models
import schemas
from settings import settings
from database import engine, get_db
from routers import users, ips, instant_access
#trans
import glob
import json
import os.path
import pyotp
from typing import Union

#Init database and tables if not exists
models.Base.metadata.create_all(bind=engine)

#Init fastapi and disable docs without login
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#Include routers
app.include_router(users.router)
app.include_router(ips.router)
app.include_router(instant_access.router)


#Mount static directory files and jinja files
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/docs")
async def get_documentation(current_user: models.User = Depends(get_current_user)):
    """Force authentication for doc page"""
    if current_user.is_admin:
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
    raise HTTPException(status_code=401, detail="Only admins can use fastapi docs")

@app.get("/openapi.json")
async def openapi(current_user: models.User = Depends(get_current_user)):
    """Force authentication for openapi page"""
    if current_user.is_admin:
        return get_openapi(title = "FastAPI", version="0.1.0", routes=app.routes)
    raise HTTPException(status_code=401, detail="Only admins can use openapi.json")


# Pages definitions

@app.get("/")
async def main(request: Request, 
db: Session = Depends(get_db),
language: dict = Depends(check_user_language)):
    """Home page get request"""
    client_host = request.client.host
    user = await check_user(request, db)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "client_host": client_host, "user": user, "language": language})

@app.post("/lang/{lang}")
async def main(request: Request,
 db: Session = Depends(get_db),
 lang: str = None,
 language: dict = Depends(check_user_language)):
    """Home page get request"""
    client_host = request.client.host
    user = await check_user(request, db)
    response = templates.TemplateResponse(
        "home.html",
        {"request": request, "client_host": client_host, "user": user, "language": language})
    response.set_cookie(
    key="lang",
    value=lang,
    httponly=True)
    return response

@app.get("/signin")
async def get_signin(request: Request,
 db: Session = Depends(get_db),
language: dict = Depends(check_user_language)):
    """Signin get request"""
    user = await check_user(request, db)
    return templates.TemplateResponse("signin.html", {"request": request, "user": user, "language": language})

@app.post("/signin")
async def post_signin(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    language: dict = Depends(check_user_language),
    two_factor_code: str = Form(""),
    form_data: OAuth2PasswordRequestForm = Depends() ):
    """Signin post request"""
    client_host = request.client.host   
    
    user = authenticate(email=form_data.username, password=form_data.password, db=db)

    if not user:
        language["warning"] = language['Incorrect-username-or-password']
        #raise HTTPException(status_code=400, detail="Incorrect username or password")  # 3
        response = templates.TemplateResponse(
        "signin.html",
        {"request": request, "client_host": client_host, "user": user, "language": language}) 
        return response

    if user.twofactor != "" and not key:
        totp = pyotp.TOTP(user.twofactor)
        if not totp.verify(two_factor_code):
            language["warning"] = language['Incorrect-totp']
            user = None
            response = templates.TemplateResponse(
            "signin.html",
            {"request": request, "client_host": client_host, "user": user, "language": language}) 
            return response

    access_token = create_access_token(sub=user.id)
    encoded_token = encoders.jsonable_encoder(access_token)
    
    for scope in form_data.scopes:
        if scope == "cli":
            return {
            "access_token": access_token
            }
    language["success"] = language['Signin-success']

    response = templates.TemplateResponse(
        "signin.html",
        {"request": request, "client_host": client_host, "user": user, "language": language})
    response.set_cookie(
    key="access_token",
    value=f"Bearer {encoded_token}",
    httponly=True)

    return response

@app.post("/token-signin")
async def post_signin(
    db: Session = Depends(get_db),
    key: str = Form(""),
    secret: str = Form("")):
    """Signin post request"""
    
    user = authenticate_by_key(key=key, secret=secret, db=db)
    
    if not user:
        return {"Auth": "Error"} 

    access_token = create_access_token(sub=user.id)
    
    return {"access_token": access_token}
    

@app.get("/logout")
async def logout(response : Response,request: Request,
 language: dict = Depends(check_user_language)):
    """logout get request"""
    client_host = request.client.host
    user = ""
    #response = RedirectResponse('/signin', status_code= 302)

    language["success"] = language['Logout-successfull']
    response = templates.TemplateResponse("home.html",
    {"request": request, "client_host": client_host, "user": user, "language": language})
    response.delete_cookie(key ='access_token')
  

    return response

@app.get("/register")
async def register(request: Request,
 db: Session = Depends(get_db),
 language: dict = Depends(check_user_language)):
    """register get request"""
    if settings.DISABLE_REGISTER:
        language["warning"] = language['Registering-disabled']

    user = await check_user(request, db)
    return templates.TemplateResponse("register.html", {"request": request, "user": user, "language": language})

@app.post("/register")
async def post_register(request: Request,
 email: str = Form(),
 password: str = Form(),
 confirm_password: str = Form(),
 db: Session = Depends(get_db),
 language: dict = Depends(check_user_language)):
    """register post request"""
    client_host = request.client.host
    user = await check_user(request, db)
    if settings.DISABLE_REGISTER:
        language["danger"] = language['Registering-disabled']
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "language": language}) 
        return response


    if user:
        language["warning"] = language['You-are-already-logged']
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "language": language}) 
        return response

    db_user = crud.get_user_by_email(db, email)

    if db_user:
        language["warning"] = language['Email-already-registered']
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "language": language}) 
        return response

    if not password_validity(password):
        language["warning"] = language['Password-help']
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "email": email, "language": language}) 
        return response

    if confirm_password != password:
        language["warning"] = language['Password-missmatch']
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "language": language}) 
        return response

    new_user = schemas.UserCreate(email=email, is_admin=False, password=password)
    user = crud.create_user(db=db, user=new_user)
    if user:
        language["success"] = language['Account-creation-successfull']
    else:
        language["danger"] = language['Account-creation-error']
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "language": language}) 
        return response
    
    access_token = create_access_token(sub=user.id)
    encoded_token = encoders.jsonable_encoder(access_token)

    response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "language": language})

    response.set_cookie(
    key="access_token",
    value=f"Bearer {encoded_token}",
    httponly=True)

    return response
    #return RedirectResponse("/signin", status_code=status.HTTP_303_SEE_OTHER)    
