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

@router.get("/config/")
def list_ips(
request: Request,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """return all ips"""
    ips = crud.get_ips(db, user = current_user)
    
    # if get request come from mysafeip-client, return json
    if request.headers.get('Cli'):
        ip_list = [{"owner": ip.owner.email, "value": ip.value,"description": ip.description} for ip in ips]
        return ip_list
    
    ip = request.client.host
    response = templates.TemplateResponse("ips.html", {"request": request, "user": current_user, "ips": ips, "ip": ip, "alert": alert})
    return response

@router.post("/config/", response_model=schemas.InstantAccess)
def post_ips(request: Request,
ip: str = Form(""),
ip_id: str = Form(""),
description: str = Form(""),
action: str = Form(""),
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """declare or delete a safe ip"""
    alert = {"success": "","danger": "","warning": ""}
    print(action)
    if action == 'delete':
        if crud.delete_ip(db, ip_id):
            alert["success"] = "ip deleted successfully"
        else:
            alert["warning"] = "An error occured while deleting ip"
        ip = request.client.host

 
    if action == 'create':
        if ip == '':
            ip = request.client.host
        
        ip_created = crud.create_user_ip(db=db, user_id=current_user.id, ip=ip, origin = "Created Manually", description=description)
        if ip_created:
            alert["success"] = str(ip_created.value) + " is now trusted"

    ips = crud.get_ips(db, user = current_user)
    response = templates.TemplateResponse("ips.html", {"request": request, "user": current_user, "ips": ips, "ip": ip, "alert": alert})
    return response



