import asyncio
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app import app
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form, UploadFile, File

from app.accessor import get_user_by_username, get_user_by_id, accessor_follow, accessor_unfollow, accessor_create_post, \
    get_post_by_id, get_all_posts, get_following_posts, accessor_add_comment, get_post_comments, \
    get_user_posts_by_username

from app.auth.database import User, get_async_session, Post

from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth.routes import fastapi_users, current_user
from app.utils import get_scaled_avatar

templates = Jinja2Templates(directory="app/templates")


@app.get('/index/{status}', response_class=HTMLResponse)
async def index(
        status: str,
        request: Request,
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    if status == 'all':
        posts = await get_all_posts(session)

    elif status == 'following':
        if current_user.following:
            posts = await get_following_posts(current_user, session)
        else:
            posts = []

    posts_with_avatars = []
    for post in posts:
        posts_with_avatars.append((get_scaled_avatar(post[0].id, (360, 240), path='C:\\Users\\oxxxysemyon\\PycharmProjects\\microblog\\avatars\\posts'), post[0]))

    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'title': 'Home',
            'current_user': current_user,
            'posts': posts,
            'posts_with_avatars': posts_with_avatars
        }
    )


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

    posts = await get_user_posts_by_username(username, session)

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
async def get_edit_profile(request: Request, current_user: User = Depends(current_user)):
    return templates.TemplateResponse(
        'edit_profile.html',
        {
            'request': request,
            'current_user': current_user
        }
    )


@app.post('/edit_profile')
async def get_edit_profile(
    request: Request,
    username: str = Form(...),
    about_me: str = Form(...),
    current_user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    stmt = update(User).where(User.id == current_user.id).values(username=username, about_me=about_me)
    await session.execute(stmt)
    await session.commit()

    return templates.TemplateResponse(
        'edit_profile.html',
        {
            'request': request,
            'current_user': current_user,
            'after_edit': True
        }
    )


@app.post('/follow')
async def follow(
        request: Request,
        username: str = Form(...),
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    await accessor_follow(current_user.id, username, session)

    return RedirectResponse(f'/user/{username}', status_code=303)


@app.post('/unfollow')
async def follow(
        request: Request,
        username: str = Form(...),
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    await accessor_unfollow(current_user.id, username, session)

    return RedirectResponse(f'/user/{username}', status_code=303)


@app.get('/user/{username}/followers')
async def list_of_followers(
        request: Request,
        username: str,
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    user = await get_user_by_username(username, session)
    if not user.followers:
        return templates.TemplateResponse(
            'list_of_users.html',
            {
                'request': request
            }
        )
    tasks = []
    for follower_id in user.followers:
        task = get_user_by_id(follower_id, session)
        tasks.append(task)
    user_followers = await asyncio.gather(*tasks)

    followers_with_avatars = []
    for follower in user_followers:
        followers_with_avatars.append((get_scaled_avatar(follower.username, (36, 36)), follower))

    return templates.TemplateResponse(
        'list_of_users.html',
        {
            'request': request,
            'followers_with_avatars': followers_with_avatars
        }
    )


@app.get('/user/{username}/following')
async def list_of_following(
        request: Request,
        username: str,
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    user = await get_user_by_username(username, session)
    tasks = []
    if not user.following:
        return templates.TemplateResponse(
            'list_of_users.html',
            {
                'request': request,
                'list_of_following': True
            }
        )
    for following_id in user.following:
        task = get_user_by_id(following_id, session)
        tasks.append(task)
    user_following = await asyncio.gather(*tasks)

    following_with_avatars = []
    for following in user_following:
        following_with_avatars.append((get_scaled_avatar(following.username, (36, 36)), following))

    return templates.TemplateResponse(
        'list_of_users.html',
        {
            'request': request,
            'followers_with_avatars': following_with_avatars
        }
    )


@app.get('/create_post')
async def create_post(
        request: Request,
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    return templates.TemplateResponse(
        'create_post.html',
        {'request': request
         }
    )


@app.post('/create_post')
async def create_post(
        request: Request,
        header: str = Form(...),
        body: str = Form(...),
        image: UploadFile = File(..., content_type="image/jpeg"),
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    post = await accessor_create_post(header, body, image, current_user, session)
    return RedirectResponse(f'/posts/{post.id}', status_code=303)


@app.get('/posts/{post_id}')
async def post(
        post_id: int,
        request: Request,
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    post = await get_post_by_id(post_id, session)
    image = get_scaled_avatar(post_id, (600, 400), path='C:\\Users\\oxxxysemyon\\PycharmProjects\\microblog\\avatars\\posts')

    comments = await get_post_comments(post_id, session)
    comments_and_avatars = []
    for comment in comments:
        comments_and_avatars.append((get_scaled_avatar(comment.author.username, size=(36, 36)), comment))
    return templates.TemplateResponse(
        'post.html',
        {
            'request': request,
            'post': post,
            'current_user': current_user,
            'image': image,
            'comments_and_avatars': comments_and_avatars
        }
    )


@app.post('/posts/add_comment/{post_id}')
async def add_comment(
        post_id: int,
        text: str = Form(...),
        current_user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    await accessor_add_comment(text, post_id, current_user, session)
    return RedirectResponse(f'/posts/{post_id}', status_code=303)

