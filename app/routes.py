import json
from typing import Annotated, Tuple, Type
from fastapi_users import FastAPIUsers, schemas, exceptions
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import app
from fastapi.responses import HTMLResponse
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

templates = Jinja2Templates(directory="app/templates")

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

current_user = fastapi_users.current_user()


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


@app.get('/login', response_class=HTMLResponse)
async def login_form(request: Request):
    print(request.url.path)
    return templates.TemplateResponse('login.html', {'request': request})


def get_auth_router(
    backend: AuthenticationBackend,
    get_user_manager: UserManagerDependency[models.UP, models.ID],
    authenticator: Authenticator,
    requires_verification: bool = False,
) -> APIRouter:
    """Generate a router with login/logout routes for an authentication backend."""
    router = APIRouter()
    get_current_user_token = authenticator.current_user_token(
        active=True, verified=requires_verification
    )

    login_responses: OpenAPIResponseType = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.LOGIN_BAD_CREDENTIALS: {
                            "summary": "Bad credentials or the user is inactive.",
                            "value": {"detail": ErrorCode.LOGIN_BAD_CREDENTIALS},
                        },
                        ErrorCode.LOGIN_USER_NOT_VERIFIED: {
                            "summary": "The user is not verified.",
                            "value": {"detail": ErrorCode.LOGIN_USER_NOT_VERIFIED},
                        },
                    }
                }
            },
        },
        **backend.transport.get_openapi_login_responses_success(),
    }

    @router.post(
        "/login",
        name=f"auth:{backend.name}.login",
        responses=login_responses,
    )
    async def login(
        request: Request,
        credentials: OAuth2PasswordRequestForm = Depends(),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
        strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        user = await user_manager.authenticate(credentials)
        if user is None or not user.is_active:
            return templates.TemplateResponse('login.html', {'request': request, 'error': 'Неверный логин или пароль'})

        if requires_verification and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
            )
        token = await strategy.write_token(user)
        response = templates.TemplateResponse('profile.html', {'request': request})
        response.set_cookie(key='auth_cookie', value=token, max_age=3600, secure=True, httponly=True)

        return response

    logout_responses: OpenAPIResponseType = {
            **{
                status.HTTP_401_UNAUTHORIZED: {
                    "description": "Missing token or inactive user."
                }
            },
            **auth_backend.transport.get_openapi_logout_responses_success(),
        }

    @router.get(
        "/logout", name=f"auth:{auth_backend.name}.logout", responses=logout_responses
    )
    async def logout(
        request: Request
    ):
        response = templates.TemplateResponse('login.html', {'request': request})
        response.delete_cookie(key='auth_cookie')
        return response

    return router


app.include_router(
    get_auth_router(auth_backend, fastapi_users.get_user_manager, fastapi_users.authenticator),
    prefix="/auth",
    tags=["auth"],
)


@app.get("/profile")
async def profile(request: Request, user: User = Depends(current_user)):
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


@app.get("/protected-route")
def protected_route(user: User = Depends(current_user)):
    return f"Hello, {user.username}"


@app.get('/user/{username}')
async def user(request: Request, username: str, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.username == username)
    res = await session.execute(query)
    user = res.scalar_one_or_none()
    print(res)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]

    return templates.TemplateResponse("user.html", {"request": request, "user": user, "posts": posts})


@app.get('/register', response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})


async def send_request(email, username, password):
    url = 'http://localhost:8000/auth/register'

    data = {
        "email": email,
        "username": username,
        "password": password
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        return response


@app.post('/register')
async def login(request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()], email: Annotated[str, Form()]):
    response = await send_request(email, username, password)
    if response.content == b'{"detail":"REGISTER_USER_ALREADY_EXISTS"}':
        return templates.TemplateResponse('register.html', {'request': request,
                                                            'error': 'Такой пользователь уже существует'})
    elif response.status_code == 422:
        return templates.TemplateResponse('register.html', {'request': request,
                                                            'error': 'Неверный email'})

    return templates.TemplateResponse('login.html', {'request': request, 'after_register':
                                                     'Вы успешно зарегистрировались. Введите учётные данные для входа'})

