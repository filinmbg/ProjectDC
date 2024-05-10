from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.entity.models import User, Role
from src.schemas.user_schemas import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    The get_user_by_email function takes an email address and returns the user associated with that email.
    If no such user exists, it returns None.

    :param email: str: Specify the email of the user to be retrieved
    :param db: AsyncSession: Pass the database session to the function
    :return: A single user object
    :doc-author: Trelent
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
    The create_user function creates a new user in the database.

    :param body: UserSchema: Validate the request body
    :param db: AsyncSession: Get the database session from the dependency injection container
    :return: A user object
    :doc-author: Trelent
    """

    user_admin = await db.execute(select(User).limit(1))
    user_obj = user_admin.scalars().first()

    if user_obj is None:
        role = Role.admin
    else:
        role = Role.user

    new_user = User(**body.model_dump(), role=role)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the refresh token for a user.

    :param user: User: Pass in the user object that is being updated
    :param token: str | None: Update the user's refresh token
    :param db: AsyncSession: Pass the database session to the function
    :return: A coroutine
    :doc-author: Trelent
    """
    user.refresh_token = token
    await db.commit()