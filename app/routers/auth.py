from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, Request, Form, encoders, Response

from auth import authenticate, authenticate_by_key, check_user, check_user_language, password_validity, create_access_token
from pydantic import ValidationError
import crud
import schemas
from database import get_db
from fastapi import APIRouter, Depends
from settings import settings
import pyotp

router = APIRouter(
    prefix="",
    tags=["register","sigin","token-sigin"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

#Mount static directory files and jinja files
router.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")


@router.get("/register")
async def register(request: Request,
 db: Session = Depends(get_db),
 language: dict = Depends(check_user_language)):
    """register get request"""
    if settings.DISABLE_REGISTER:
        language["warning"] = language['Registering-disabled']

    user = await check_user(request, db)
    return templates.TemplateResponse("register.html", {"request": request, "user": user, "language": language})

@router.post("/register")
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

    try:
        new_user = schemas.UserCreate(email=email, is_admin=False, password=password)
    except ValidationError as v:
        if "value_error.email" in str(v):
            language["danger"] = language['Account-creation-error'] + ": check mail"
        else:
            language["danger"] = language['Account-creation-error'] + ": " + v
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "client_host": client_host, "user": user, "language": language}) 
        return response

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

@router.get("/signin")
async def get_signin(request: Request,
 db: Session = Depends(get_db),
language: dict = Depends(check_user_language)):
    """Signin get request"""
    user = await check_user(request, db)
    return templates.TemplateResponse("signin.html", {"request": request, "user": user, "language": language})

@router.post("/signin")
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
        response = templates.TemplateResponse(
        "signin.html",
        {"request": request, "client_host": client_host, "user": user, "language": language}) 
        return response

    if user.twofactor != "":
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

@router.post("/token-signin")
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
    

@router.get("/logout")
async def logout(response : Response,request: Request,
 language: dict = Depends(check_user_language)):
    """logout get request"""
    client_host = request.client.host
    user = ""
    language["success"] = language['Logout-successfull']
    response = templates.TemplateResponse("home.html",
    {"request": request, "client_host": client_host, "user": user, "language": language})
    response.delete_cookie(key ='access_token')
  

    return response