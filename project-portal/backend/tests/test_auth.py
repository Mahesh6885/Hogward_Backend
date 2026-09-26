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

    def test_sorting_ceremony_workflow(self, client, ai_user, admin_user):
        token = get_token(client, "aiuser", "userpass123")
        admin_token = get_token(client, "admin", "adminpass123")
        # Check initial state
        resp = client.get("/api/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["sorting_ceremony_completed"] is False

        # Complete ceremony
        resp_comp = client.post("/api/projects/me/complete-sorting-ceremony", headers=auth_headers(token))
        assert resp_comp.status_code == 200
        assert resp_comp.json()["success"] is True

        # Verify completed
        resp2 = client.get("/api/auth/me", headers=auth_headers(token))
        assert resp2.json()["data"]["sorting_ceremony_completed"] is True

        # Admin reset ceremony
        resp_reset = client.post(f"/api/admin/teams/{ai_user.id}/reset-sorting-ceremony", headers=auth_headers(admin_token))
        assert resp_reset.status_code == 200
        assert resp_reset.json()["data"]["sorting_ceremony_completed"] is False

        # Verify reset
        resp3 = client.get("/api/auth/me", headers=auth_headers(token))
        assert resp3.json()["data"]["sorting_ceremony_completed"] is False
