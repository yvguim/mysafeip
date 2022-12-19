import models
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi import Depends, HTTPException, Request, Form

from auth import get_current_user, check_user, check_user_language
import crud
import models
import schemas
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from settings import settings
import json
import glob
import os

router = APIRouter(
    prefix="/instant-access",
    tags=["instant-access"],
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
async def get_create_instant_access(request: Request,
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """Create an instant access link to share with others"""
    alert = {"success": "","danger": "","warning": ""}
    language = await check_user_language(request)
    links = crud.get_links(db, user = current_user)
    return templates.TemplateResponse("instant_access.html", {"request": request, "user": current_user, "link": "https://your_secure_url", "url_website": settings.URL_WEBSITE, "links": links, "alert": alert, "language": languages[language]})

@router.post("/config/", response_model=schemas.InstantAccess)
async def post_instant_access(request: Request,
link: str = Form(""),
description: str = Form(""),
action: str = Form(""),
db: Session = Depends(get_db),
current_user: models.User = Depends(get_current_user)):
    """declare a new link"""
    alert = {"success": "","danger": "","warning": ""}
    language = await check_user_language(request)
    print(action)
    if action == 'delete':
        if crud.delete_link(db, link):
            alert["success"] = "Instant link deleted successfully"
        else:
            alert["warning"] = "An error occured while deleting Instant link"

    if action == 'create':
        link_created = crud.create_instant_access(db=db, link=link, user_id=current_user.id, description=description)
        if link_created:
            alert["success"] = str(link_created.link) + " is now accessible directly from " + str(link_created.unique_link)
    links = crud.get_links(db, user = current_user)
    return templates.TemplateResponse("instant_access.html", {"request": request, "user": current_user, "link": "https://destination_url","url_website": settings.URL_WEBSITE, "links": links, "alert": alert, "language": languages[language]})

@router.get("/ia/{unique_link}")
async def get_link_redirect(request: Request,
unique_link: str,
db: Session = Depends(get_db),
):
    """Create an instant access link to share with others"""
    alert = {"success": "","danger": "","warning": ""}
    language = await check_user_language(request)
    destination_link = crud.get_link_by_unique_link(db, unique_link = unique_link)

    if not destination_link:
        alert["warning"] = "Sorry this link does not exists"
        client_host = request.client.host
        user = await check_user(request, db)
        return templates.TemplateResponse(
        "home.html",
        {"request": request, "client_host": client_host, "user": user, "alert": alert})
    
    owner_id = destination_link.owner_id
    ip = request.client.host
    crud.create_user_ip(db=db, user_id=owner_id, ip=ip, origin=unique_link, description="Added by instant_access")
    alert["success"] = "We are allowing you ip: " + str(ip) +". You will be redirected to " + destination_link.link +" in 10 seconds"
    
    return templates.TemplateResponse(
        "redirect.html",
        {"request": request, "link": destination_link.link, "alert": alert, "language": languages[language]})