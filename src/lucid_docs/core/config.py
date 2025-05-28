from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LucidDocs"
    TEMP_STORAGE_PATH: str = "./temp"
    CHROMA_COLLECTION_NAME: str = "pdf_documents"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    LLM_MODEL: str = "gemini-2.0-flash"
    LOG_FORMAT: str = "json"
    LOG_LEVEL: str = "INFO"
    MONGO_URI: str = "mongodb://localhost:27017/lucid_docs"
    MONGO_DB_NAME: str = "lucid_docs"


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()