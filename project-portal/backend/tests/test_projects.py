"""Tests for project submission and retrieval."""
import pytest
from tests.conftest import get_token, auth_headers


class TestProjectSubmission:
    def test_ai_user_submits_ai_topic(self, client, ai_user, ai_topics, domains):
        token = get_token(client, "aiuser", "userpass123")
        topic_id = ai_topics[0].id
        resp = client.post(
            "/api/projects",
            json={"topic_id": topic_id},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["topic_id"] == topic_id
        assert data["status"] == "SUBMITTED"
        assert data["current_round"] == 1
        assert data["project_code"].startswith("PRJ-")
        assert data["custom_topic"] is None

    def test_cyber_user_submits_cyber_topic(self, client, cyber_user, cyber_topics, domains):
        token = get_token(client, "cyberuser", "userpass123")
        resp = client.post(
            "/api/projects",
            json={"topic_id": cyber_topics[0].id},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["domain"]["name"] == "CYBERSECURITY"

    def test_oi_user_submits_custom_topic(self, client, oi_user, domains):
        token = get_token(client, "oiuser", "userpass123")
        resp = client.post(
            "/api/projects",
            json={"custom_topic": "AI Based Smart Agriculture Monitoring System"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["custom_topic"] == "AI Based Smart Agriculture Monitoring System"
        assert data["topic_id"] is None

    def test_user_cannot_submit_second_project(self, client, ai_user, ai_topics, domains):
        token = get_token(client, "aiuser", "userpass123")
        client.post("/api/projects", json={"topic_id": ai_topics[0].id}, headers=auth_headers(token))
        resp = client.post("/api/projects", json={"topic_id": ai_topics[1].id}, headers=auth_headers(token))
        assert resp.status_code == 409
        assert "already have a project" in resp.json()["message"]

    def test_oi_user_must_provide_custom_topic(self, client, oi_user, domains):
        token = get_token(client, "oiuser", "userpass123")
        resp = client.post("/api/projects", json={"topic_id": None, "custom_topic": None}, headers=auth_headers(token))
        assert resp.status_code == 400

    def test_oi_user_custom_topic_too_short(self, client, oi_user, domains):
        token = get_token(client, "oiuser", "userpass123")
        resp = client.post("/api/projects", json={"custom_topic": "Short"}, headers=auth_headers(token))
        assert resp.status_code == 422

    def test_project_code_is_unique(self, client, ai_user, cyber_user, ai_topics, cyber_topics, domains):
        t1 = get_token(client, "aiuser", "userpass123")
        t2 = get_token(client, "cyberuser", "userpass123")
        r1 = client.post("/api/projects", json={"topic_id": ai_topics[0].id}, headers=auth_headers(t1))
        r2 = client.post("/api/projects", json={"topic_id": cyber_topics[0].id}, headers=auth_headers(t2))
        assert r1.json()["data"]["project_code"] != r2.json()["data"]["project_code"]


class TestGetMyProject:
    def test_user_gets_own_project(self, client, ai_user, ai_topics, domains):
        token = get_token(client, "aiuser", "userpass123")
        client.post("/api/projects", json={"topic_id": ai_topics[0].id}, headers=auth_headers(token))
        resp = client.get("/api/projects/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["user"]["username"] == "aiuser"

    def test_user_with_no_project_gets_404(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/projects/me", headers=auth_headers(token))
        assert resp.status_code == 404

    def test_unauthenticated_cannot_get_project(self, client):
        resp = client.get("/api/projects/me")
        assert resp.status_code == 403
