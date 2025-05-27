from fastapi.testclient import TestClient
from lucid_docs.src.lucid_docs.main import app

client = TestClient(app)

def test_upload_pdf():
    with open("tests/teste_upload.pdf", "rb") as f:
        response = client.post(
            "/upload/pdf",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    assert response.status_code == 200