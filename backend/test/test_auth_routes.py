import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_success(client):
    resp = client.post(
        "/api/register",
        data={"email": "a@b.com", "username": "alice", "password": "pw1233456"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "a@b.com"
    assert body["username"] == "alice"
    assert "id" in body

def test_register_duplicate_email(client):
    client.post("/api/register", data={"email": "a@b.com", "username": "alice", "password": "pw1233456"})
    resp = client.post("/api/register", data={"email": "a@b.com", "username": "alice2", "password": "pw1233456"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Email already registered"

def test_login_invalid_credentials(client):
    # user doesn't exist
    resp = client.post("/api/login", json={"email": "no@no.com", "password": "pw12334562224324"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"
