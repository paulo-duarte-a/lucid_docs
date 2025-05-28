import pytest
from fastapi.testclient import TestClient
from lucid_docs.main import create_app
from lucid_docs.routers import authentication
from lucid_docs.models.database import User

@pytest.fixture
def client():
    app = create_app()
    yield TestClient(app)

def test_login_for_access_token_success(monkeypatch, client):
    async def dummy_authenticate_user(username, password):
        class DummyUser:
            pass
        dummy = DummyUser()
        dummy.username = username
        return dummy
    monkeypatch.setattr(authentication, "authenticate_user", dummy_authenticate_user)
    monkeypatch.setattr(authentication, "create_access_token", lambda data, expires_delta: "dummy_token")

    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "secret", "grant_type": "password"},
    )
    assert response.status_code == 200
    assert response.json() == {"access_token": "dummy_token", "token_type": "bearer"}

def test_login_for_access_token_failure(monkeypatch, client):
    async def dummy_authenticate_user_fail(username, password):
        return None
    monkeypatch.setattr(authentication, "authenticate_user", dummy_authenticate_user_fail)

    response = client.post(
        "/auth/token",
        data={"username": "wronguser", "password": "wrongpass", "grant_type": "password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_read_users_me(client):
    async def dummy_get_current_active_user():
        return User(
            username="testuser",
            full_name="Test User",
            email="test@example.com",
            disabled=False,
        )
    client.app.dependency_overrides[authentication.get_current_active_user] = dummy_get_current_active_user

    response = client.get("/auth/users/me/")
    assert response.status_code == 200
    assert response.json() == {
        '_id': None,
        'username': 'testuser',
        'email': 'test@example.com',
        'full_name': 'Test User',
        'disabled': False
    }
    client.app.dependency_overrides = {}
