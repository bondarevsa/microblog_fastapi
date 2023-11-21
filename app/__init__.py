from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.auth import auth_backend
from app.auth.database import User
from app.auth.manager import get_user_manager
from app.auth.schemas import UserRead, UserCreate

app = FastAPI(title='Micro Blog')

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "static"),
    name="static",
)

from app import routes
from app.auth import routes
from app import middlewares
