import re
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]
"""
A custom type for a MongoDB ObjectID represented as a string.
"""

class User(BaseModel):
    """
    Model representing a user.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Unique username for authentication"
    )
    email: Optional[EmailStr] = Field(default=None)
    full_name: Optional[str] = Field(default=None)
    disabled: Optional[bool] = Field(default=False, description="Indicates whether the user account is disabled")


class UserInDB(User):
    """
    Model representing a user stored in the database, including password information.
    """
    password: str = Field(
        min_length=8,
        max_length=128,
        description="User's password, must contain at least 8 characters, one uppercase letter, one lowercase letter, one digit, and one special character"
    )

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        """
        Validates the password to ensure it meets complexity requirements.

        Raises:
            ValueError: If the password does not meet the required complexity.
        
        Returns:
            str: The validated password.
        """
        if len(value) < 8:
            raise ValueError("Password must contain at least 8 characters")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must include at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must include at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must include at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must include at least one special character")
        return value


class Message(BaseModel):
    """
    Model representing a message within a conversation.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    chat_id: str = Field(
        description="UUID of the conversation associated with this message"
    )
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Sender's username"
    )
    role: str = Field(
        description="User's role (e.g., 'user', 'assistant')"
    )
    content: str = Field(
        description="Content of the message"
    )
    timestamp: str = Field(
        description="Timestamp of the message in ISO 8601 format"
    )
    
    @field_validator("chat_id")
    def validate_chat_id(cls, value: str | None) -> str | None:
        """
        Validates that the chat_id, if provided, is a UUID version 4.

        Args:
            value (str | None): The str to validate.

        Returns:
            str | None: The validated str.

        Raises:
            ValueError: If the tr is provided and is not a UUID version 4.
        """
        if value is not None and UUID(value).version != 4:
            raise ValueError("str must be UUID version 4.")
        return value


class Conversation(BaseModel):
    """
    Model representing a conversation between users.
    """
    messages: list[Message]