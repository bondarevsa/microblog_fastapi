from pydantic import BaseModel


class LoginForm(BaseModel):
    username: str = 'pudge'
    password: str = '123'
    remember_me: bool = False
