"""Tests for topic random selection and admin topic management."""
import pytest
from tests.conftest import get_token, auth_headers


class TestRandomTopics:
    def test_ai_user_gets_10_ai_topics(self, client, ai_user, ai_topics, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/topics/random", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) == 10
        # All topics must be AI domain
        for topic in data["data"]:
            assert topic["domain"]["name"] == "AI"

    def test_cyber_user_gets_10_cyber_topics(self, client, cyber_user, cyber_topics, domains):
        token = get_token(client, "cyberuser", "userpass123")
        resp = client.get("/api/topics/random", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 10
        for topic in data["data"]:
            assert topic["domain"]["name"] == "CYBERSECURITY"

    def test_oi_user_cannot_get_random_topics(self, client, oi_user, domains):
        token = get_token(client, "oiuser", "userpass123")
        resp = client.get("/api/topics/random", headers=auth_headers(token))
        assert resp.status_code == 403
        assert "Open Innovation" in resp.json()["message"]

    def test_ai_user_cannot_get_cyber_topics_via_query_param(self, client, ai_user, ai_topics, cyber_topics, domains):
        """
        SECURITY: Even if an AI user tries ?domain=CYBERSECURITY, the backend
        always uses the authenticated user's domain.
        """
        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/topics/random?domain=CYBERSECURITY", headers=auth_headers(token))
        assert resp.status_code == 200
        # Should still return AI topics (query param ignored)
        for topic in resp.json()["data"]:
            assert topic["domain"]["name"] == "AI"

    def test_insufficient_topics_returns_error(self, client, ai_user, domains, db):
        """If fewer than 10 topics exist, return 422 with a meaningful error."""
        from app.models.topic import Topic
        # Only create 5 AI topics
        ai_domain_id = domains["ai"].id
        for i in range(5):
            db.add(Topic(title=f"AI Topic {i}", domain_id=ai_domain_id, is_active=True))
        db.commit()

        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/topics/random", headers=auth_headers(token))
        assert resp.status_code == 422
        assert "Not enough" in resp.json()["message"]

    def test_unauthenticated_cannot_get_topics(self, client):
        resp = client.get("/api/topics/random")
        assert resp.status_code == 403


class TestAdminTopics:
    def test_admin_creates_ai_topic(self, client, admin_user, domains):
        token = get_token(client, "admin", "adminpass123")
        resp = client.post(
            "/api/admin/topics",
            json={"title": "Quantum AI", "description": "Quantum computing meets AI.", "domain": "AI"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["title"] == "Quantum AI"

    def test_normal_user_cannot_create_topic(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.post(
            "/api/admin/topics",
            json={"title": "Rogue Topic", "domain": "AI"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    def test_admin_can_deactivate_topic(self, client, admin_user, ai_topics, domains):
        token = get_token(client, "admin", "adminpass123")
        topic_id = ai_topics[0].id
        resp = client.patch(
            f"/api/admin/topics/{topic_id}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    def test_deactivated_topic_not_in_random(self, client, admin_user, ai_user, ai_topics, domains, db):
        """Deactivated topics must not appear in random selection."""
        token_admin = get_token(client, "admin", "adminpass123")
        token_user = get_token(client, "aiuser", "userpass123")

        # Deactivate 5 topics so 10 remain
        for t in ai_topics[:5]:
            client.patch(
                f"/api/admin/topics/{t.id}/status",
                json={"is_active": False},
                headers=auth_headers(token_admin),
            )

        resp = client.get("/api/topics/random", headers=auth_headers(token_user))
        assert resp.status_code == 200
        active_ids = {t.id for t in ai_topics[5:]}
        for topic in resp.json()["data"]:
            assert topic["id"] in active_ids
