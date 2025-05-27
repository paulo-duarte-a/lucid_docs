from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Número de chunks relevantes a serem recuperados do banco vetorial"
    )


class QueryResponse(BaseModel):
    results: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False


class UserInDB(User):
    password: str