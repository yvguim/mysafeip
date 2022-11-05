import models
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi import Depends, HTTPException, Request, Form

from auth import get_current_user
import crud
import models
import schemas
from database import get_db
from fastapi import APIRouter, Depends, HTTPException


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
def read_users(request: Request, skip: int = 0,
limit: int = 100,
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


@router.get("/users/{user_id}", response_model=schemas.User)
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

@router.post("/read", tags=["users"])
def delete_users(request: Request,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """read and return all users"""
    alert = {"success": "","danger": "","warning": ""}
    user = current_user
    
    if not current_user.is_admin:
        alert["warning"] = "Only admin can delete users"

    if crud.delete_user(db, email):
        alert["success"] = "User " + email + " deleted successfully"
    else:
        alert["warning"] = "An error occured while deleting" + email
    users = crud.get_users(db)
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "user": user, "alert": alert})