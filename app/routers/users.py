import models
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Depends, Request, Form, APIRouter, Depends
from fastapi.responses import RedirectResponse
from auth import get_current_user, check_user_language, password_validity
import crud
import models
import schemas
from database import get_db
import pyotp

alert = {"success": "","danger": "","warning": ""}

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

#Mount static directory files and jinja files
router.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

@router.get("/read", tags=["users"])
async def read_users(request: Request,
db: Session = Depends(get_db),
language: dict = Depends(check_user_language),
current_user: models.User = Depends(get_current_user)):
    """read and return all users"""

    user = current_user
    if current_user.is_admin:
        users = crud.get_users(db)
    else:
        users = []
        language["warning"] = language["Only admin can get users"]

    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "user": user, "language": language})



@router.post("/read", tags=["users"])
async def delete_users(request: Request,
 db: Session = Depends(get_db),
 language: dict = Depends(check_user_language),
 email: str = Form(),
 current_user: models.User = Depends(get_current_user)):
    """read and return all users"""
    user = current_user
    users = ""
    # non admin user can't delete other account
    if (not user.is_admin) and (user.email != email):
        language["warning"] = language["Only-admin-can-delete-other-users"]
        return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": "", "user": user, "language": language})

    # admin can't delete his own account
    if (user.is_admin) and (user.email == email):
        language["warning"] = language["you-cant-delete-your-own-admin-account"]
        users = crud.get_users(db)
        return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "user": user, "language": language})

    if crud.delete_user(db, email):
        language["success"] = language["User"] + " " + email + language["deleted-successfully"]
    else:
        language["warning"] = language["An-error-occured-while-deleting"] + email
    
    if user.is_admin:
        users = crud.get_users(db)
    else:
        response = RedirectResponse('/', status_code= 302)
        response.delete_cookie(key ='access_token')
        return response


    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "user": user, "language": language})


@router.get("/reset_password/{user_id}")
async def reset_password(user_id: int,
 request: Request,
 current_user: models.User = Depends(get_current_user),
 db: Session = Depends(get_db),
 language: dict = Depends(check_user_language)):
    """register get request"""
    
    if not current_user.is_admin and (current_user != user_id):
        language["danger"] = language["You-are-not-allowed-to-do-this"]
        user = False
        return templates.TemplateResponse("reset_password.html", {"request": request, "user": user, "language": language})
    
    user = crud.get_user(db, user_id)
    return templates.TemplateResponse("reset_password.html", {"request": request, "user": user, "language": language})

@router.post("/reset_password/{user_id}")
async def post_reset_password(user_id: int,
 request: Request,
 current_user: models.User = Depends(get_current_user),
 password: str = Form(),
 confirm_password: str = Form(),
 db: Session = Depends(get_db),
 language: dict = Depends(check_user_language)):
    """register post request"""
    if not current_user.is_admin and (current_user != user_id):
        language["danger"] = language["You-are-not-allowed-to-do-this"]
        user = False
        return templates.TemplateResponse("reset_password.html", {"request": request, "user": user, "language": language})

    user = crud.get_user(db, user_id)
    if not password_validity(password):
        language["warning"] = language["Password-help"]
        response = templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "alert": alert, "user": user, "language": language}) 
        return response

    if confirm_password != password:
        language["warning"] = language["Password-missmatch"]
        response = templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "alert": alert, "user": user, "language": language}) 
        return response
    if (user.id != current_user.id) and (not current_user.is_admin):
        language["danger"] = language["You-are-not-allowed-to-do-this"]
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "alert": alert, "user": current_user, "language": language}) 
        return response
    user = crud.reset_user_password(db=db, user=user, password=password)

    if not user:
        language["danger"] = language["An-error-occured-during-password-reset"]
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "alert": alert, "user": current_user, "language": language}) 
        return response
    
    language["success"] = language["Password-reset-successfull"]
    response = templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "alert": alert, "user": user, "language": language}) 
    return response


@router.get("/details/{user_id}", response_model=schemas.User)
async def user_details(user_id: int,
 request: Request,
 db: Session = Depends(get_db),
 language: dict = Depends(check_user_language),
 current_user: models.User = Depends(get_current_user)):
    """search and return one user by id"""
    if current_user.is_admin:
        user = crud.get_user(db, user_id=user_id)
    else:
        user = current_user
    if user is None:
        language["warning"] = language["User-does-not-exist"]
        user = None 
    twofactorurl = ""
    tokens = crud.get_tokens(db, user)

    return templates.TemplateResponse("user-details.html", {"request": request, "user": user, "tokens": tokens, "language": language})

@router.post("/details/{user_id}")
async def user_details(user_id: int,
 request: Request,
 twofactor: bool = Form(""),
 token: bool = Form(""),
 action: str = Form(""),
 token_id = Form(""),
 description: str = Form(""),
 current_user: models.User = Depends(get_current_user),
 db: Session = Depends(get_db),
 language: dict = Depends(check_user_language)):
    """register get request"""
    twofactorurl = ""
    newtoken = ""

    if current_user.is_admin:
        user = crud.get_user(db, user_id=user_id)
    else:
        user = current_user
    
    if action == 'delete':
        if crud.delete_token(db, token_id):
            language["success"] = language["Instant-link-deleted-successfully"]
        else:
            language["warning"] = language["An-error-occured-while-deleting-Instant-link"]

    if token:
        newtoken = crud.create_new_token(db, user.id, description)

    if twofactor and user.twofactor == "":
        crud.enable_user_twofactor(db, user)
        twofactorurl = pyotp.totp.TOTP(user.twofactor).provisioning_uri(name=user.email,issuer_name='MySafeIP')

    if not twofactor and user.twofactor != "" and action != 'delete':
        crud.disable_user_twofactor(db, user)

    tokens = crud.get_tokens(db, user)
    
    return templates.TemplateResponse("user-details.html", {"request": request, "user": user, "twofactorurl": twofactorurl, "newtoken": newtoken, "tokens": tokens, "language": language})
