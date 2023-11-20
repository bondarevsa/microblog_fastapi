from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app import User
from app.auth.database import Post


async def get_user_by_id(user_id: int, session: AsyncSession):
    query = select(User).where(User.id == user_id)
    res = await session.execute(query)
    return res.scalar_one_or_none()


async def get_user_by_username(username: str, session: AsyncSession):
    query = select(User).where(User.username == username)
    res = await session.execute(query)
    return res.scalar_one_or_none()


async def accessor_follow(follower_user_id, following_user_username, session):
    following_user = await get_user_by_username(following_user_username, session)
    stmt = update(User).values(followers=func.array_append(User.followers, follower_user_id)).where(
        User.username == following_user_username)
    await session.execute(stmt)
    stmt = update(User).values(following=func.array_append(User.following, following_user.id)).where(
        User.id == follower_user_id)
    await session.execute(stmt)
    await session.commit()


async def accessor_unfollow(follower_user_id, following_user_username, session):
    following_user = await get_user_by_username(following_user_username, session)
    stmt = update(User).values(followers=func.array_remove(User.followers, follower_user_id)).where(
        User.username == following_user_username)
    await session.execute(stmt)
    stmt = update(User).values(following=func.array_remove(User.following, following_user.id)).where(
        User.id == follower_user_id)
    await session.execute(stmt)
    await session.commit()


async def accessor_create_post(header, body, image, current_user, session):
    post = Post(body=body, header=header, user_id=current_user.id)
    session.add(post)
    await session.flush()
    with open(f"avatars/posts/{post.id}.jpg", 'wb') as image_file:
        image_file.write(image.file.read())
    await session.commit()
    return post


async def get_post_by_id(post_id: int, session: AsyncSession):
    query = select(Post).where(Post.id == post_id)
    res = await session.execute(query)
    res = res.scalar_one_or_none()
    return res


async def get_all_posts(session):
    query = select(Post).order_by(desc(Post.timestamp))
    res = await session.execute(query)
    posts = res.all()
    return posts


async def get_following_posts(current_user: User, session: AsyncSession):
    query = select(Post).where(Post.user_id.in_(current_user.following)).order_by(desc(Post.timestamp))
    res = await session.execute(query)
    posts = res.all()
    return posts
