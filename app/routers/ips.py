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

alert = {"success": "","danger": "","warning": ""}

router = APIRouter(
    prefix="/ips",
    tags=["ips"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

#Mount static directory files and jinja files
router.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

@router.get("/create_ip/", response_model=schemas.Ip)
def get_create_ip(request: Request,
current_user: models.User = Depends(get_current_user)):
    """declare one ip"""
    
    ip = request.client.host
    return templates.TemplateResponse("create_ip.html", {"request": request, "user": current_user, "ip": ip, "alert": alert})


@router.post("/create_ip/", response_model=schemas.Ip)
def post_create_ip(request: Request,
ip: str = Form(""),
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """declare one ip"""
    
    if ip == '':
        ip = request.client.host
        
    ip_created = crud.create_user_ip(db=db, user_id=current_user.id, ip=ip)
    if ip_created:
        alert["success"] = str(ip_created.value) + " is now trusted"
    response = templates.TemplateResponse("create_ip.html", {"request": request, "user": current_user, "ip": ip, "alert": alert})
    return response


@router.get("/get_ips/")
def read_ips(
request: Request,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """return all ips"""
    ips = crud.get_ips(db, user = current_user)
    
    # if get request come from mysafeip-client, return json
    if request.headers.get('Cli'):
        ip_list = [{"owner": ip.owner.email, "value": ip.value,"description": ip.description} for ip in ips]
        return ip_list

    response = templates.TemplateResponse("ips.html", {"request": request, "user": current_user, "ips": ips, "alert": alert})
    return response

@router.post("/get_ips/")
def delete_ips(request: Request,
ip: str = Form(),
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """read and return all users"""

    if crud.delete_ip(db, ip):
        alert["success"] = "ip deleted successfully"
    else:
        alert["warning"] = "An error occured while deleting ip"
    ips = crud.get_ips(db, current_user)
    
    response = templates.TemplateResponse("ips.html", {"request": request, "user": current_user, "ips": ips, "alert": alert})

    return response


