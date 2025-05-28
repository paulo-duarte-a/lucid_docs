import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
from lucid_docs.main import create_app
from lucid_docs.models.database import UserInDB, User
from lucid_docs.core.config import settings

mock_users_collection = AsyncMock()
mock_chroma = MagicMock()
mock_llm = MagicMock()

@pytest.fixture
def client():
    app = create_app()

    app.dependency_overrides.update({
        "lucid_docs.dependencies.users_collection": lambda: mock_users_collection,
        "lucid_docs.dependencies.chroma": lambda: mock_chroma,
        "lucid_docs.dependencies.llm": lambda: mock_llm,
    })
    
    return TestClient(app)

@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer mock_token"}

def mock_user():
    return UserInDB(
        username="testuser",
        password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # senha: secret
        disabled=False
    )

@pytest.mark.asyncio
async def test_login_success(client):
    mock_users_collection.find_one.return_value = mock_user().dict()
    
    response = client.post("/auth/token", data={"username": "testuser", "password": "secret"})
    
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    mock_users_collection.find_one.return_value = None
    
    response = client.post("/auth/token", data={"username": "wrong", "password": "wrong"})
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

@pytest.mark.asyncio
async def test_register_user(client):
    mock_users_collection.find_one.return_value = None
    mock_users_collection.insert_one = AsyncMock()
    
    user_data = {
        "username": "newuser",
        "password": "ValidPass123!",
        "email": "new@example.com"
    }
    
    response = client.post("/auth/users/register/", json=user_data)
    
    assert response.status_code == 200
    assert response.json()["username"] == "newuser"

def test_upload_pdf(client, auth_header):
    test_file = ("file", ("test.pdf", open("tests/test.pdf", "rb"), "application/pdf"))
    
    with patch("lucid_docs.utils.storage.save_temp_file") as mock_save:
        mock_save.return_value = "/tmp/mock.pdf"
        mock_chroma.add_documents = AsyncMock()
        
        response = client.post(
            "/upload/pdf",
            files={"file": test_file},
            headers=auth_header
        )
        
        assert response.status_code == 200
        assert "metadata" in response.json()

def test_upload_invalid_file(client, auth_header):
    test_file = ("file", ("test.txt", open("tests/test.txt", "rb"), "text/plain"))
    
    response = client.post(
        "/upload/pdf",
        files={"file": test_file},
        headers=auth_header
    )
    
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["error"]

def test_get_current_user(client, auth_header):
    with patch("lucid_docs.core.security.get_current_active_user") as mock_user:
        mock_user.return_value = User(username="testuser")
        
        response = client.get("/auth/users/me/", headers=auth_header)
        
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"

def test_query_endpoint(client, auth_header):
    mock_rag_chain = AsyncMock(return_value="mock response")
    mock_llm.ainvoke = mock_rag_chain
    
    query_data = {"question": "test question", "top_k": 3}
    
    response = client.post("/chat/", json=query_data, headers=auth_header)
    
    assert response.status_code == 200
    assert response.json()["results"] == "mock response"

@pytest.fixture
def mock_dependencies():
    with patch("lucid_docs.dependencies.GoogleGenerativeAIEmbeddings") as mock_embeddings, \
         patch("lucid_docs.dependencies.ChatGoogleGenerativeAI") as mock_llm, \
         patch("lucid_docs.dependencies.AsyncIOMotorClient") as mock_mongo:
        
        mock_embeddings.return_value = MagicMock()
        mock_llm.return_value = MagicMock()
        mock_mongo.return_value = MagicMock()
        
        yield

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}