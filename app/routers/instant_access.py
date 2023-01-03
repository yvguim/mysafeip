import models
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi import Depends, Request, Form

from auth import get_current_user, check_user, check_user_language
import crud
import models
import schemas
from database import get_db
from fastapi import APIRouter, Depends
from settings import settings

router = APIRouter(
    prefix="/instant-access",
    tags=["instant-access"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

#Mount static directory files and jinja files
router.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

@router.get("/config/")
async def get_create_instant_access(request: Request,
db: Session = Depends(get_db),
language: dict = Depends(check_user_language),
current_user: models.User = Depends(get_current_user)):
    """Create an instant access link to share with others"""
    links = crud.get_links(db, user = current_user)
    return templates.TemplateResponse("instant_access.html", {"request": request, "user": current_user, "link": "https://your_secure_url", "url_website": settings.URL_WEBSITE, "links": links, "language": language})

@router.post("/config/", response_model=schemas.InstantAccess)
async def post_instant_access(request: Request,
link: str = Form(""),
description: str = Form(""),
action: str = Form(""),
db: Session = Depends(get_db),
language: dict = Depends(check_user_language),
current_user: models.User = Depends(get_current_user)):
    """declare a new link"""
    if action == 'delete':
        if crud.delete_link(db, link):
            language["success"] = language["Instant-link-deleted-successfully"]
        else:
            language["warning"] = language["An-error-occured-while-deleting-Instant-link"]

    if action == 'create':
        link_created = crud.create_instant_access(db=db, link=link, user_id=current_user.id, description=description)
        if link_created:
            language["success"] = str(link_created.link) + language["is-now-accessible-directly-from"] + str(link_created.unique_link)
    links = crud.get_links(db, user = current_user)
    return templates.TemplateResponse("instant_access.html", {"request": request, "user": current_user, "link": "https://destination_url","url_website": settings.URL_WEBSITE, "links": links, "language": language})

@router.get("/ia/{unique_link}")
async def get_link_redirect(request: Request,
unique_link: str,
db: Session = Depends(get_db),
language: dict = Depends(check_user_language)
):
    """Create an instant access link to share with others"""
    client_host = request.client.host
    destination_link = crud.get_link_by_unique_link(db, unique_link = unique_link)

    if not destination_link:
        language["warning"] = language["Sorry-this-link-does-not-exists"]
        client_host = request.client.host
        user = await check_user(request, db)
        return templates.TemplateResponse(
        "home.html",
        {"request": request, "client_host": client_host, "user": user, "language": language})
    
    owner_id = destination_link.owner_id
    ip = request.client.host
    crud.create_user_ip(db=db, user_id=owner_id, ip=ip, origin=unique_link, description="Added by instant_access")
    language["success"] = language['We-are-allowing-your-ip']+": " + str(ip) +". "+ language['You-will-be-redirected-to'] + destination_link.link + language['in-10-seconds']
    
    return templates.TemplateResponse(
        "redirect.html",
        {"request": request, "link": destination_link.link, "language": language, "client_host": client_host})