from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app import User


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
