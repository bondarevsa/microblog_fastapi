from typing import Annotated
from fastapi_users import FastAPIUsers, models

from app import app
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form

from app.auth.auth import auth_backend
from app.auth.database import User
from app.auth.manager import get_user_manager
from app.auth.schemas import UserRead, UserCreate, UserUpdate

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_users.authentication import AuthenticationBackend, Authenticator, Strategy
from fastapi_users.manager import BaseUserManager, UserManagerDependency
from fastapi_users.openapi import OpenAPIResponseType
from fastapi_users.router.common import ErrorCode, ErrorModel

from app.utils import send_request

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


@app.get('/login', response_class=HTMLResponse)
async def login_form(request: Request):
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
        response = RedirectResponse('/index/all', status_code=303)
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


@app.get('/register', response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})


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

