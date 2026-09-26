"""Tests for authentication endpoints."""
import pytest
from tests.conftest import get_token, auth_headers


class TestLogin:
    def test_admin_login_success(self, client, admin_user):
        resp = client.post("/api/auth/login", json={"username": "admin", "password": "adminpass123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["user"]["role"] == "ADMIN"

    def test_user_login_success(self, client, ai_user):
        resp = client.post("/api/auth/login", json={"username": "aiuser", "password": "userpass123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["user"]["role"] == "USER"
        assert data["data"]["user"]["domain"] == "AI"

    def test_invalid_password(self, client, admin_user):
        resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpass"})
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    def test_invalid_username(self, client, admin_user):
        resp = client.post("/api/auth/login", json={"username": "nonexistent", "password": "adminpass123"})
        assert resp.status_code == 401

    def test_inactive_user_blocked(self, client, inactive_user):
        resp = client.post("/api/auth/login", json={"username": "inactive", "password": "userpass123"})
        assert resp.status_code == 403
        assert "inactive" in resp.json()["message"].lower()


class TestMe:
    def test_get_me_authenticated(self, client, ai_user):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "aiuser"

    def test_get_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 403

    def test_get_me_invalid_token(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401
