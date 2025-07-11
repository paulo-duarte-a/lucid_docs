"""
Dependencies Module

This module configures all the external services and libraries used by the application,
including authentication with OAuth2, password hashing, database connections (MongoDB), 
and integration with language models and vector databases.
"""

import os

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from langchain_chroma import Chroma
from chromadb import PersistentClient
from lucid_docs.core.config import settings
from lucid_docs.core.database import get_users_collection, get_messages_collection

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Application secret key and algorithm used for token generation.
# use openssl to generate a secure key:
# openssl rand -hex 32
SECRET_KEY = os.getenv('SECRET_KEY', 'acc16580347786582c001ac2d186dd4a52791d9ba1674974dcbf5ba302b0f6e0')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

embeddings = None  # Global variable to hold the embeddings service instance

def get_embeddings():
    # Initialize embeddings service for Google Generative AI
    global embeddings

    if embeddings:
        return embeddings

    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=settings.GEMINI_API_KEY
    )
    return embeddings

llm = None  # Global variable to hold the language model instance

def get_llm():
    # Initialize language model for Google Generative AI
    global llm
    if llm:
        return llm

    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0
    )
    return llm

chroma = None  # Global variable to hold the Chroma instance

def get_chroma():
    global chroma
    if chroma:
        return chroma

    # Persistent client for Chroma
    client = PersistentClient(path=settings.CHROMA_PERSIST_DIR)

    # Chroma instance linking the persistent client with the embeddings function for document collections
    chroma = Chroma(
        client=client,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=get_embeddings()
    )
    return chroma


async def get_users_collection_dep() -> AsyncIOMotorClient:
    return await get_users_collection()


async def get_messages_collection_dep() -> AsyncIOMotorClient:
    return await get_messages_collection()