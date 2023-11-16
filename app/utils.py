import base64
from io import BytesIO

from PIL import Image
import os


def get_scaled_avatar(username, size=(100, 100)):
    avatar_path = os.path.join('C:\\Users\\oxxxysemyon\\PycharmProjects\\microblog\\avatars', f"{username}.jpg")

    if not os.path.exists(avatar_path):
        avatar_path = os.path.join('C:\\Users\\oxxxysemyon\\PycharmProjects\\microblog\\avatars', f"default.jpg")

    with Image.open(avatar_path) as img:
        scaled_img = img.resize(size)
        with BytesIO() as buffer:
            scaled_img.save(buffer, format="JPEG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
