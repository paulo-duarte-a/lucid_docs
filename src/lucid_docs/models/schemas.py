from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class QueryRequest(BaseModel):
    """
    Request model for a query operation.

    Attributes:
        question (str): The question to be queried.
        top_k (int): Number of relevant chunks to retrieve from the vector database.
        chat_id (str): UUID of the chat to associate the query.
    """
    question: str
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of relevant chunks to retrieve from the vector database"
    )
    chat_id: str = Field(
        description="UUID of the chat to associate the query"
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


class QueryResponse(BaseModel):
    """
    Response model for a query operation.

    Attributes:
        results (str): The query results.
    """
    results: str


class Token(BaseModel):
    """
    Model representing the access token information.

    Attributes:
        access_token (str): The access token.
        token_type (str): The type of token.
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Model representing token data, primarily for user identification.

    Attributes:
        username (str | None): The username associated with the token (optional).
    """
    username: str | None = None
