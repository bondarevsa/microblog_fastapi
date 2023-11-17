import base64
import json
from io import BytesIO
from typing import Annotated, Tuple, Type
from fastapi_users import FastAPIUsers, schemas, exceptions
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import app
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app.models.models import user as users

from app.auth.auth import auth_backend
from app.auth.database import User, get_async_session
from app.auth.manager import get_user_manager
from app.auth.schemas import UserRead, UserCreate, UserUpdate

from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_users import models
from fastapi_users.authentication import AuthenticationBackend, Authenticator, Strategy
from fastapi_users.manager import BaseUserManager, UserManagerDependency
from fastapi_users.openapi import OpenAPIResponseType
from fastapi_users.router.common import ErrorCode, ErrorModel
from app.auth.routes import fastapi_users, current_user
from app.utils import get_scaled_avatar

templates = Jinja2Templates(directory="app/templates")


@app.get('/index', response_class=HTMLResponse)
def index(request: Request):
    user = {'username': 'pudge'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        },
        {
            'author': {'username': 'Ипполит'},
            'body': 'Какая гадость эта ваша заливная рыба!!'
        }
    ]
    return templates.TemplateResponse('index.html', {'request': request,
                                                                    'title': 'Home',
                                                                    'user': user,
                                                                    'posts': posts})


@app.get('/user/{username}')
async def user(
        request: Request,
        username: str,
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    query = select(User).where(User.username == username)
    res = await session.execute(query)
    user = res.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]

    avatar = get_scaled_avatar(user.username, (128, 128))
    avatar_mini = get_scaled_avatar(user.username, (36, 36))

    return templates.TemplateResponse(
        "user.html",
        {
            "request": request,
            "user": user,
            "posts": posts,
            "avatar": avatar,
            "avatar_mini": avatar_mini,
            "current_user": current_user,
        }
    )


@app.get('/edit_profile')
async def get_edit_profile(request: Request, user: User = Depends(current_user)):
    return templates.TemplateResponse(
        'edit_profile.html',
        {
            'request': request,
            'user': user
        }
    )


@app.post('/edit_profile')
async def get_edit_profile(
    request: Request,
    username: str = Form(...),
    about_me: str = Form(...),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    stmt = update(User).where(User.id == user.id).values(username=username, about_me=about_me)
    await session.execute(stmt)
    await session.commit()
    return templates.TemplateResponse('edit_profile.html', {'request': request, 'user': user, 'after_edit': True})


@app.get("/protected-route")
def protected_route(user: User = Depends(current_user)):
    return f"Hello, {user.email}"
