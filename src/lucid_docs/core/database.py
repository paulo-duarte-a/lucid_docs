import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from lucid_docs.core.config import settings


logger = logging.getLogger(__name__)

class Database:
    _instance: Optional['Database'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    
    def __new__(cls) -> 'Database':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self) -> None:
        if self._client is not None:
            logger.warning("Database connection already established.")
            return
        
        try:
            self._client = AsyncIOMotorClient(
                settings.MONGO_URI,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
                
                retryWrites=True,
                retryReads=True,
                
                heartbeatFrequencyMS=10000,
            )
            
            await self._client.server_info()
            
            self._database = self._client[settings.MONGO_DB_NAME]
            
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        
    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("Database connection closed.")
    
    async def _create_indexes(self) -> None:
        
        try:
            users_collection = self._database["users"]
            await users_collection.create_index("username", unique=True)
            await users_collection.create_index("email", unique=True, sparse=True)
            
            messages_collection = self._database["messages"]
            await messages_collection.create_index([("username", 1), ("chat_id", 1)])
            await messages_collection.create_index([("chat_id", 1), ("timestamp", 1)])
            await messages_collection.create_index("timestamp")
            
            logger.info("Indexes created successfully.")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            
    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        return self._database

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        if self._database is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        return self._database[collection_name]

    async def health_check(self) -> bool:
        """
        Perform a health check to ensure the database connection is active.
        
        Returns:
            bool: True if the database is reachable, False otherwise.
        """
        try:
            await self.client.server_info()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


database = Database()


async def get_database() -> AsyncIOMotorClient:
    return database.database


async def get_users_collection() -> AsyncIOMotorCollection:
    return database.get_collection("users")


async def get_messages_collection() -> AsyncIOMotorCollection:
    return database.get_collection("messages")
