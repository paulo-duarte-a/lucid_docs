from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from lucid_docs.models.schemas import TokenData
from lucid_docs.models.database import User, UserInDB
from lucid_docs.dependencies import pwd_context
from lucid_docs.dependencies import SECRET_KEY, ALGORITHM
from lucid_docs.dependencies import oauth2_scheme
from lucid_docs.core.database import database


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the plain password matches the hashed password.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a hashed password from a plain password.

    Args:
        password (str): The plain text password.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


async def get_user(username: str) -> Optional[UserInDB]:
    """
    Retrieve a user from the database by username.

    Args:
        username (str): The user's username.

    Returns:
        Optional[UserInDB]: The user object if found, None otherwise.
    """
    users_collection = database.get_collection("users")
    user_data = await users_collection.find_one({"username": username})
    if user_data is not None:
        return UserInDB(**user_data)
    return None


async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user by verifying the username and password.

    Args:
        username (str): The user's username.
        password (str): The user's plain text password.

    Returns:
        Optional[UserInDB]: The authenticated user object if credentials are valid, None otherwise.
    """
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JSON Web Token (JWT) access token.

    Args:
        data (dict[str, Any]): The payload data to encode in the token.
        expires_delta (Optional[timedelta], optional): Time delta for token expiration. Defaults to 15 minutes if not provided.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    """
    Decode the JWT token and retrieve the current user.

    Args:
        token (Annotated[str, Depends(oauth2_scheme)]): The JWT bearer token.

    Raises:
        HTTPException: If the credentials are invalid or token is expired.

    Returns:
        UserInDB: The current authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Ensure that the current user is active.

    Args:
        current_user (Annotated[User, Depends(get_current_user)]): The current user object.

    Raises:
        HTTPException: If the user account is inactive.

    Returns:
        User: The current active user.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user