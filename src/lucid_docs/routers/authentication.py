"""
Authentication routes for user login, registration, and retrieval of current user information.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from lucid_docs.core.security import get_password_hash
from lucid_docs.models.database import User, UserInDB
from lucid_docs.models.schemas import Token
from lucid_docs.dependencies import users_collection

from lucid_docs.core.security import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
)

ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Authenticate user and return an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form data containing username and password.

    Raises:
        HTTPException: If the username or password is incorrect, responding with status code 401.

    Returns:
        Token: A token object containing the access token and its type.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Retrieve the current active user's information.

    Args:
        current_user (User): The currently authenticated active user.

    Returns:
        User: The user data.
    """
    return current_user


@router.post("/users/register/", response_model=User)
async def register_user(
    user: UserInDB,
):
    """
    Register a new user.

    Args:
        user (UserInDB): The user data for registration.

    Raises:
        HTTPException: If the username is already registered with status code 400.

    Returns:
        User: The registered user data.
    """
    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user.password = get_password_hash(user.password)
    await users_collection.insert_one(user.dict())

    return User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        disabled=user.disabled,
    )
