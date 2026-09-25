"""Tests for project submission, drafts, and retrieval."""
import pytest
from tests.conftest import get_token, auth_headers


class TestProjectSubmission:
    def test_user_saves_draft(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.patch(
            "/api/projects/me/draft",
            json={
                "project_title": "AI Autonomous Drone",
                "abstract": "An innovative autonomous drone solution",
                "proposed_solution": "Using computer vision models",
                "technology_stack": ["Python", "OpenCV", "PyTorch"],
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["project_title"] == "AI Autonomous Drone"
        assert data["status"] == "DRAFT"

    def test_user_submits_project(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.post(
            "/api/projects",
            json={
                "project_title": "Final AI Solution",
                "abstract": "Complete submission abstract",
                "github_url": "https://github.com/example/ai-project",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "SUBMITTED"
        assert data["is_submitted"] is True
        assert data["current_round"] == 1
        assert data["project_code"].startswith("PRJ-")
        assert data["realm"] == "AI"

    def test_submitted_project_cannot_be_re_submitted_without_permission(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        # First submission
        client.post(
            "/api/projects",
            json={"project_title": "First AI Solution", "github_url": "https://github.com/example/ai-first"},
            headers=auth_headers(token),
        )
        # Attempt second submission
        resp = client.post(
            "/api/projects",
            json={"project_title": "Second AI Solution"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "PROJECT_EXISTS"

    def test_project_code_is_unique(self, client, ai_user, cyber_user, domains):
        t1 = get_token(client, "aiuser", "userpass123")
        t2 = get_token(client, "cyberuser", "userpass123")
        r1 = client.get("/api/projects/me", headers=auth_headers(t1))
        r2 = client.get("/api/projects/me", headers=auth_headers(t2))
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["data"]["project_code"] != r2.json()["data"]["project_code"]


class TestGetMyProject:
    def test_user_gets_own_project(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/projects/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["user"]["username"] == "aiuser"
        assert resp.json()["data"]["realm"] == "AI"

    def test_unauthenticated_cannot_get_project(self, client):
        resp = client.get("/api/projects/me")
        assert resp.status_code == 403
