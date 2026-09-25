"""Tests for admin user management."""
import pytest
from tests.conftest import get_token, auth_headers


class TestCreateUser:
    def test_admin_creates_user(self, client, admin_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Test User",
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123",
                "phone": "9876543210",
                "organization": "Test Org",
                "domain": "AI",
                "role": "USER",
                "status": "ACTIVE",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"
        assert "password" not in data["data"]
        assert "password_hash" not in data["data"]

    def test_non_admin_cannot_create_user(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Test User",
                "username": "anotheruser",
                "email": "another@example.com",
                "password": "testpass123",
                "domain": "AI",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    def test_duplicate_username_rejected(self, client, admin_user, ai_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Another AI User",
                "username": "aiuser",  # already exists
                "email": "newemail@example.com",
                "password": "testpass123",
                "domain": "AI",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 409
        assert "username" in resp.json()["message"].lower()

    def test_duplicate_email_rejected(self, client, admin_user, ai_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Another AI User",
                "username": "brand_new_user",
                "email": "ai@test.com",  # already used by ai_user
                "password": "testpass123",
                "domain": "AI",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 409

    def test_invalid_domain_rejected(self, client, admin_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Test User",
                "username": "testuser2",
                "email": "test2@example.com",
                "password": "testpass123",
                "domain": "INVALID_DOMAIN",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    def test_password_never_returned(self, client, admin_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Secure User",
                "username": "secureuser",
                "email": "secure@example.com",
                "password": "SuperSecret123",
                "domain": "CYBERSECURITY",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        raw = resp.text
        assert "SuperSecret123" not in raw
        assert "password_hash" not in raw


class TestListUsers:
    def test_admin_lists_users(self, client, admin_user, ai_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.get("/api/admin/users", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_user_cannot_list_users(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/admin/users", headers=auth_headers(token))
        assert resp.status_code == 403


class TestUpdateUserStatus:
    def test_admin_deactivates_user(self, client, admin_user, ai_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.patch(
            f"/api/admin/users/{ai_user.id}/status",
            json={"status": "INACTIVE"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "INACTIVE"

    def test_deactivated_user_cannot_login(self, client, admin_user, ai_user, domains):
        token = get_token(client, "admin", "adminpass123")
        client.patch(
            f"/api/admin/users/{ai_user.id}/status",
            json={"status": "INACTIVE"},
            headers=auth_headers(token),
        )
        resp = client.post("/api/auth/login", json={"username": "aiuser", "password": "userpass123"})
        assert resp.status_code == 403


class TestPasswordReset:
    def test_admin_resets_password(self, client, admin_user, ai_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.patch(
            f"/api/admin/users/{ai_user.id}/password",
            json={"new_password": "newpassword123"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        # Old password should no longer work
        login = client.post("/api/auth/login", json={"username": "aiuser", "password": "userpass123"})
        assert login.status_code == 401
        # New password should work
        login2 = client.post("/api/auth/login", json={"username": "aiuser", "password": "newpassword123"})
        assert login2.status_code == 200


class TestDeleteUser:
    def test_admin_deletes_team(self, client, admin_user, ai_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.delete(f"/api/admin/teams/{ai_user.id}", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify user is gone
        get_resp = client.get(f"/api/admin/teams/{ai_user.id}", headers=auth_headers(token))
        assert get_resp.status_code == 404

    def test_admin_deletes_user_endpoint(self, client, admin_user, cyber_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.delete(f"/api/admin/users/{cyber_user.id}", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_admin_cannot_delete_self(self, client, admin_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.delete(f"/api/admin/teams/{admin_user.id}", headers=auth_headers(token))
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "SELF_DELETE"

    def test_non_admin_cannot_delete_user(self, client, ai_user, cyber_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.delete(f"/api/admin/teams/{cyber_user.id}", headers=auth_headers(token))
        assert resp.status_code == 403

    def test_delete_nonexistent_user_returns_404(self, client, admin_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.delete("/api/admin/teams/99999", headers=auth_headers(token))
        assert resp.status_code == 404
