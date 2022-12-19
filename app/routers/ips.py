import models
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi import Depends, HTTPException, Request, Form

from auth import get_current_user, check_user_language
import crud
import models
import schemas
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
import json
import glob
import os

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

#trans
app_language = 'en'
languages = {}
language_list = glob.glob("languages/*.json")
for lang in language_list:
    filename  = os.path.basename(lang)
    lang_code, ext = os.path.splitext(filename)

    with open(lang, 'r', encoding='utf8') as file:
        languages[lang_code] = json.load(file)


@router.get("/config/")
async def list_ips(
request: Request,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """return all ips"""
    ips = crud.get_ips(db, user = current_user)
    language = await check_user_language(request)
    # if get request come from mysafeip-client, return json
    if request.headers.get('Cli'):
        ip_list = [{"owner": ip.owner.email, "value": ip.value,"description": ip.description} for ip in ips]
        return ip_list
    
    ip = request.client.host
    response = templates.TemplateResponse("ips.html", {"request": request, "user": current_user, "ips": ips, "ip": ip, "alert": alert, "language": languages[language]})
    return response

@router.post("/config/", response_model=schemas.InstantAccess)
async def post_ips(request: Request,
ip: str = Form(""),
ip_id: str = Form(""),
description: str = Form(""),
action: str = Form(""),
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """declare or delete a safe ip"""
    alert = {"success": "","danger": "","warning": ""}
    language = await check_user_language(request)
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
    response = templates.TemplateResponse("ips.html", {"request": request, "user": current_user, "ips": ips, "ip": ip, "alert": alert, "language": languages[language]})
    return response



