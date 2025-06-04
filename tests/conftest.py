# In tests/conftest.py

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from lucid_docs.main import create_app # Assuming this is needed for 'app' fixture
from lucid_docs.core.config import settings as global_app_settings
from lucid_docs.core.database import database as global_db_manager_singleton, Database as CoreDatabaseClass

# _MOCKED_DB_NAME and patch_non_db_settings_for_test_session fixture remain the same...
_MOCKED_DB_NAME = "mocked_lucid_docs_db"

@pytest.fixture(scope="session", autouse=True)
def patch_non_db_settings_for_test_session(tmp_path_factory):
    original_chroma_persist_dir = global_app_settings.CHROMA_PERSIST_DIR
    original_temp_storage_path = global_app_settings.TEMP_STORAGE_PATH
    original_mongo_db_name = global_app_settings.MONGO_DB_NAME

    global_app_settings.MONGO_DB_NAME = _MOCKED_DB_NAME
    
    test_chroma_dir = tmp_path_factory.mktemp("chroma_db_test_data")
    global_app_settings.CHROMA_PERSIST_DIR = str(test_chroma_dir)
    
    test_temp_dir = tmp_path_factory.mktemp("temp_storage_test_data")
    global_app_settings.TEMP_STORAGE_PATH = str(test_temp_dir)

    yield

    global_app_settings.CHROMA_PERSIST_DIR = original_chroma_persist_dir
    global_app_settings.TEMP_STORAGE_PATH = original_temp_storage_path
    global_app_settings.MONGO_DB_NAME = original_mongo_db_name


@pytest.fixture(scope="function", autouse=True)
def mock_database_operations(patch_non_db_settings_for_test_session):
    mock_motor_db_instance = MagicMock(name="MockAsyncIOMotorDatabase")
    mock_motor_db_instance.name = _MOCKED_DB_NAME
    # Initialize a cache for collection mocks on the DB instance mock itself
    mock_motor_db_instance._collection_mocks_cache = {} # Cache here

    mock_motor_client_instance = MagicMock(name="MockAsyncIOMotorClient")
    patch_async_motor_client_class = patch('lucid_docs.core.database.AsyncIOMotorClient', return_value=mock_motor_client_instance)

    async def new_connect_mock_with_self(self_instance, *args, **kwargs):
        self_instance._client = mock_motor_client_instance
        self_instance._database = mock_motor_db_instance
        if not hasattr(mock_motor_client_instance, 'server_info') or not isinstance(mock_motor_client_instance.server_info, AsyncMock):
             mock_motor_client_instance.server_info = AsyncMock()
        await self_instance._create_indexes()

    patch_connect = patch.object(CoreDatabaseClass, 'connect', new=new_connect_mock_with_self)
    patch_disconnect = patch.object(CoreDatabaseClass, 'disconnect', new_callable=AsyncMock)
    patch_create_indexes = patch.object(CoreDatabaseClass, '_create_indexes', new_callable=AsyncMock)
    patch_health_check = patch.object(CoreDatabaseClass, 'health_check', new_callable=AsyncMock, return_value=True)

    # Corrected new_get_collection_mock to cache and reuse collection mocks
    def new_get_collection_mock(instance_self, collection_name: str):
        # Use the cache on the mock_motor_db_instance
        if collection_name not in mock_motor_db_instance._collection_mocks_cache:
            coll_mock = MagicMock(name=f"MockCollection_{collection_name}")
            coll_mock.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_inserted_id"))
            coll_mock.find_one = AsyncMock(return_value=None)  # Default
            
            find_result_mock = MagicMock()
            find_result_mock.to_list = AsyncMock(return_value=[])
            find_result_mock.sort = MagicMock(return_value=find_result_mock)
            find_result_mock.limit = MagicMock(return_value=find_result_mock)
            coll_mock.find = MagicMock(return_value=find_result_mock)
            
            coll_mock.delete_many = AsyncMock(return_value=MagicMock(deleted_count=0))
            coll_mock.update_one = AsyncMock()
            coll_mock.create_index = AsyncMock()
            
            aggregate_result_mock = MagicMock()
            aggregate_result_mock.to_list = AsyncMock(return_value=[])
            coll_mock.aggregate = MagicMock(return_value=aggregate_result_mock)
            
            mock_motor_db_instance._collection_mocks_cache[collection_name] = coll_mock
            # Also make it accessible via attribute for convenience (e.g., db.users)
            setattr(mock_motor_db_instance, collection_name, coll_mock)
        
        return mock_motor_db_instance._collection_mocks_cache[collection_name]

    patch_get_collection = patch.object(CoreDatabaseClass, 'get_collection', new=new_get_collection_mock)

    # Start patches (rest of the fixture setup)
    active_patch_motor_client_class = patch_async_motor_client_class.start()
    active_patch_connect = patch_connect.start()
    # ... (start other patches) ...
    active_patch_disconnect = patch_disconnect.start()
    active_patch_create_indexes = patch_create_indexes.start()
    active_patch_health_check = patch_health_check.start()
    active_patch_get_collection = patch_get_collection.start()

    yield {
        "motor_client_class": active_patch_motor_client_class,
        "motor_client_instance": mock_motor_client_instance,
        "db_instance": mock_motor_db_instance, # This is the mock_motor_db_instance with _collection_mocks_cache
        "connect": active_patch_connect,
        "disconnect": active_patch_disconnect,
        "create_indexes": active_patch_create_indexes,
        "health_check": active_patch_health_check,
        "get_collection": active_patch_get_collection
    }

    # Stop patches (rest of the fixture teardown)
    patch_get_collection.stop()
    patch_health_check.stop()
    # ... (stop other patches) ...
    patch_create_indexes.stop()
    patch_disconnect.stop()
    patch_connect.stop()
    patch_async_motor_client_class.stop()
    
    for attr_name in ['_client', '_database']:
        if attr_name in global_db_manager_singleton.__dict__:
            try:
                delattr(global_db_manager_singleton, attr_name)
            except AttributeError:
                pass

# The app, client, and db fixtures remain the same as in the previous correct version
# For example, the db fixture:
@pytest.fixture(scope="function")
def app(mock_database_operations): # Ensures mock_database_operations has run
    app_instance = create_app()
    return app_instance

@pytest.fixture(scope="function")
def client(app): # Depends on app fixture
    from fastapi.testclient import TestClient # Ensure TestClient is imported
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="function")
def db(client, mock_database_operations): # Depends on client (for app startup) and mock_database_operations
    assert hasattr(global_db_manager_singleton, '_database') and \
           global_db_manager_singleton._database is mock_database_operations["db_instance"], \
        "Database manager's internal database is not the expected mock instance from mock_database_operations."
    yield mock_database_operations["db_instance"]