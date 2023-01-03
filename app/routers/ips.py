import models
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi import Depends, Request, Form

from auth import get_current_user, check_user_language
import crud
import models
import schemas
from database import get_db
from fastapi import APIRouter, Depends

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
async def list_ips(
request: Request,
db: Session = Depends(get_db),
language: dict = Depends(check_user_language),
current_user: models.User = Depends(get_current_user)):
    """return all ips"""
    ips = crud.get_ips(db, user = current_user)
    # if get request come from mysafeip-client, return json
    if request.headers.get('Cli'):
        ip_list = [{"owner": ip.owner.email, "value": ip.value,"description": ip.description} for ip in ips]
        return ip_list
    
    ip = request.client.host
    response = templates.TemplateResponse("ips.html", {"request": request, "user": current_user, "ips": ips, "ip": ip, "language": language})
    return response

@router.post("/config/", response_model=schemas.InstantAccess)
async def post_ips(request: Request,
ip: str = Form(""),
ip_id: str = Form(""),
description: str = Form(""),
action: str = Form(""),
db: Session = Depends(get_db),
language: dict = Depends(check_user_language),
current_user: models.User = Depends(get_current_user)):
    """declare or delete a safe ip"""
    if action == 'delete':
        if crud.delete_ip(db, ip_id):
            language["success"] = language["ip-deleted-successfully"]
        else:
            language["warning"] = language["An-error-occured-while-deleting-ip"]
        ip = request.client.host
 
    if action == 'create':
        if ip == '':
            ip = request.client.host
        
        ip_created = crud.create_user_ip(db=db, user_id=current_user.id, ip=ip, origin = language["Created-Manually"], description=description)
        if ip_created:
            language["success"] = str(ip_created.value) + language["is-now-trusted"]

    ips = crud.get_ips(db, user = current_user)
    response = templates.TemplateResponse("ips.html", {"request": request, "user": current_user, "ips": ips, "ip": ip, "language": language})
    return response



