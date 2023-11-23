from datetime import datetime

from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import update

from app import app
from fastapi import Request, HTTPException

from app.auth.database import get_async_session, User
from app.utils import get_user_id_by_jwt

templates = Jinja2Templates(directory="app/templates")


@app.middleware("http")
async def set_last_seen_time(request: Request, call_next):
    user_id = get_user_id_by_jwt(request)
    async for session in get_async_session():
        if user_id:
            query = update(User).where(User.id == user_id).values(last_seen=datetime.utcnow())
            await session.execute(query)
            await session.commit()
    return await call_next(request)


@app.exception_handler(HTTPException)
async def not_found_error(request, exc: HTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse('/errors/404.html', {"request": request}, status_code=404)
    if exc.status_code == 401:
        return RedirectResponse('/login', status_code=303)
    print(exc.detail)
    return templates.TemplateResponse('/errors/500.html', {"request": request}, status_code=500)


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):
    print(exc)
    return templates.TemplateResponse('/errors/500.html', {"request": request}, status_code=500)
