import base64
import json
from io import BytesIO
from fastapi import Request
import httpx
from PIL import Image
import os
import jwt


def get_scaled_avatar(username, size=(100, 100)):
    avatar_path = os.path.join('C:\\Users\\oxxxysemyon\\PycharmProjects\\microblog\\avatars', f"{username}.jpg")

    if not os.path.exists(avatar_path):
        avatar_path = os.path.join('C:\\Users\\oxxxysemyon\\PycharmProjects\\microblog\\avatars', f"default.jpg")

    with Image.open(avatar_path) as img:
        scaled_img = img.resize(size)
        with BytesIO() as buffer:
            scaled_img.save(buffer, format="JPEG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")


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


def get_user_id_by_jwt(request: Request):
    if 'auth_cookie' in request.cookies:
        auth_jwt_token: str = request.cookies['auth_cookie']
        decoded_jwt = jwt.decode(auth_jwt_token, 'SECRET', algorithms=['HS256'], audience="fastapi-users:auth")
        user_id = int(decoded_jwt['sub'])
        return user_id
    return None
