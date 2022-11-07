import models
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Depends, Request, Form, APIRouter, Depends
from fastapi.responses import RedirectResponse

from auth import get_current_user, check_user, password_validity
import crud
import models
import schemas
from database import get_db

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
def read_users(request: Request,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """read and return all users"""
    alert = {"success": "","danger": "","warning": ""}
    user = current_user
    if current_user.is_admin:
        users = crud.get_users(db)
    else:
        users = []
        alert["warning"] = "Only admin can get users"

    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "user": user, "alert": alert})


@router.get("/details/{user_id}", response_model=schemas.User)
def read_user_details(user_id: int,
request: Request,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """search and return one user by id"""
    alert = {"success": "","danger": "","warning": ""}
    if current_user.is_admin:
        user_details = crud.get_user(db, user_id=user_id)
    else:
        user_details = current_user
    if user_details is None:
        alert["warning"] = "User does not exist."
        user_details = None 
    return templates.TemplateResponse(
        "user_details.html",
        {"request": request, "user_details": user_details, "user": current_user, "alert": alert})

@router.post("/read", tags=["users"])
def delete_users(request: Request,
db: Session = Depends(get_db),
email: str = Form(),
current_user: models.User = Depends(get_current_user)):
    """read and return all users"""
    alert = {"success": "","danger": "","warning": ""}
    user = current_user
    users = ""
    # non admin user can't delete other account
    if (not user.is_admin) and (user.email != email):
        alert["warning"] = "Only admin can delete other users"
        return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": "", "user": user, "alert": alert})

    # admin can't delete his own account
    if (user.is_admin) and (user.email == email):
        alert["warning"] = "you can't delete your own admin account"
        users = crud.get_users(db)
        return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "user": user, "alert": alert})

    if crud.delete_user(db, email):
        alert["success"] = "User " + email + " deleted successfully"
    else:
        alert["warning"] = "An error occured while deleting" + email
    
    if user.is_admin:
        users = crud.get_users(db)
    else:
        response = RedirectResponse('/', status_code= 302)
        response.delete_cookie(key ='access_token')
        return response


    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "user": user, "alert": alert})


@router.get("/reset_password/{user_id}")
async def reset_password(user_id: int, request: Request, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db),):
    """register get request"""
    alert = {"success": "","danger": "","warning": ""}
    print(user_id)
    user = crud.get_user(db, user_id)

    return templates.TemplateResponse("reset_password.html", {"request": request, "user": user, "alert": alert})

@router.post("/reset_password/{user_id}")
async def post_reset_password(user_id: int,request: Request, current_user: models.User = Depends(get_current_user), password: str = Form(), confirm_password: str = Form(), db: Session = Depends(get_db)):
    """register post request"""
    alert = {"success": "","danger": "","warning": ""}
    user = crud.get_user(db, user_id)
    if not password_validity(password):
        alert["warning"] = "Password must be 6 characters minimum, contain lower case, upper case, a number and special character."
        response = templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "alert": alert, "user": user}) 
        return response

    if confirm_password != password:
        alert["warning"] = "Password missmatch!"
        response = templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "alert": alert, "user": user}) 
        return response
    if (user.id != current_user.id) and (not current_user.is_admin):
        alert["danger"] = "You are not allowed to reset other users passwords"
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "alert": alert, "user": current_user}) 
        return response
    user = crud.reset_user_password(db=db, user=user, password=password)
    print(user)

    if not user:
        alert["danger"] = "An error occured during password reset."
        response = templates.TemplateResponse(
        "register.html",
        {"request": request, "alert": alert, "user": current_user}) 
        return response
    
    alert["success"] = "Password reset successfull."
    response = templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "alert": alert, "user": user}) 
    return response