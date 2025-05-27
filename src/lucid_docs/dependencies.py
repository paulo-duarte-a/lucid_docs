import os

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from lucid_docs.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

fake_users_db = {
}

SECRET_KEY = os.getenv('SECRET_KEY', 'acc16580347786582c001ac2d186dd4a52791d9ba1674974dcbf5ba302b0f6e0')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.EMBEDDING_MODEL,
    google_api_key=settings.GEMINI_API_KEY
)

llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0
)