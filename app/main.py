"""
Main MySafeIP API pages
"""
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi import Depends, FastAPI, HTTPException, Request
from auth import get_current_user, check_user, check_user_language
import models
from database import engine, get_db
from routers import users, ips, instant_access, auth

#Init database and tables if not exists
models.Base.metadata.create_all(bind=engine)

#Init fastapi and disable docs without login
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#Include routers
app.include_router(users.router)
app.include_router(ips.router)
app.include_router(instant_access.router)
app.include_router(auth.router)


#Mount static directory files and jinja files
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/docs")
async def get_documentation(current_user: models.User = Depends(get_current_user)):
    """Force authentication for doc page"""
    if current_user.is_admin:
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
    raise HTTPException(status_code=401, detail="Only admins can use fastapi docs")

@app.get("/openapi.json")
async def openapi(current_user: models.User = Depends(get_current_user)):
    """Force authentication for openapi page"""
    if current_user.is_admin:
        return get_openapi(title = "FastAPI", version="0.1.0", routes=app.routes)
    raise HTTPException(status_code=401, detail="Only admins can use openapi.json")

@app.get("/")
async def main(request: Request, 
db: Session = Depends(get_db),
language: dict = Depends(check_user_language)):
    """Home page get request"""
    client_host = request.client.host
    user = await check_user(request, db)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "client_host": client_host, "user": user, "language": language})

@app.get("/lang/{lang}")
async def main(request: Request,
 db: Session = Depends(get_db),
 lang: str = None,
 language: dict = Depends(check_user_language)):
    """Home page get request"""
    client_host = request.client.host
    user = await check_user(request, db)
    response = templates.TemplateResponse(
        "home.html",
        {"request": request, "client_host": client_host, "user": user, "language": language})
    response.set_cookie(
    key="lang",
    value=lang,
    httponly=True)
    return response



 
