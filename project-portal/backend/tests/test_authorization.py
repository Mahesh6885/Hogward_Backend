"""
Critical authorization tests.

Validates that security boundaries are strictly enforced:
- USER cannot access ADMIN endpoints
- AI user cannot use Cybersecurity topics
- Cybersecurity user cannot use AI topics
- Open Innovation user cannot use predefined topics
- User cannot access another user's data
"""
from tests.conftest import get_token, auth_headers


class TestRoleBasedAccess:
    def test_user_cannot_access_admin_users(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        assert client.get("/api/admin/users", headers=auth_headers(token)).status_code == 403

    def test_user_cannot_access_admin_projects(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        assert client.get("/api/admin/projects", headers=auth_headers(token)).status_code == 403

    def test_user_cannot_access_admin_dashboard(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        assert client.get("/api/admin/dashboard", headers=auth_headers(token)).status_code == 403

    def test_user_cannot_create_topic(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.post("/api/admin/topics", json={"title": "Rogue Topic", "domain": "AI"}, headers=auth_headers(token))
        assert resp.status_code == 403

    def test_unauthenticated_blocked(self, client):
        assert client.get("/api/admin/dashboard").status_code == 403
        assert client.get("/api/admin/users").status_code == 403
        assert client.get("/api/projects/me").status_code == 403


class TestDomainBasedAccess:
    def test_ai_user_cannot_submit_cyber_topic(self, client, ai_user, cyber_topics, domains):
        """
        CRITICAL SECURITY: AI user tries to submit a Cybersecurity topic.
        Backend must detect the domain mismatch and return 403.
        """
        token = get_token(client, "aiuser", "userpass123")
        resp = client.post(
            "/api/projects",
            json={"topic_id": cyber_topics[0].id},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "DOMAIN_MISMATCH"

    def test_cyber_user_cannot_submit_ai_topic(self, client, cyber_user, ai_topics, domains):
        """
        CRITICAL SECURITY: Cybersecurity user tries to submit an AI topic.
        Backend must detect the domain mismatch and return 403.
        """
        token = get_token(client, "cyberuser", "userpass123")
        resp = client.post(
            "/api/projects",
            json={"topic_id": ai_topics[0].id},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "DOMAIN_MISMATCH"

    def test_oi_user_cannot_use_predefined_topic(self, client, oi_user, ai_topics, domains):
        """
        Open Innovation user cannot bypass by submitting a predefined topic.
        """
        token = get_token(client, "oiuser", "userpass123")
        resp = client.post(
            "/api/projects",
            json={"topic_id": ai_topics[0].id},
            headers=auth_headers(token),
        )
        # OI user must provide custom_topic, not topic_id
        assert resp.status_code in (400, 403)

    def test_oi_user_cannot_get_random_predefined_topics(self, client, oi_user, ai_topics, domains):
        token = get_token(client, "oiuser", "userpass123")
        resp = client.get("/api/topics/random", headers=auth_headers(token))
        assert resp.status_code == 403

    def test_random_topic_domain_param_ignored(self, client, ai_user, ai_topics, cyber_topics, domains):
        """
        SECURITY: Even with ?domain=CYBERSECURITY in the URL, AI user should only get AI topics.
        The domain is determined from the JWT, not from the query parameter.
        """
        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/topics/random?domain=CYBERSECURITY", headers=auth_headers(token))
        assert resp.status_code == 200
        for topic in resp.json()["data"]:
            assert topic["domain"]["name"] == "AI", "Domain bypass attempt should not work"


class TestOwnershipChecks:
    def test_user_can_view_own_project(self, client, ai_user, ai_topics, domains):
        token = get_token(client, "aiuser", "userpass123")
        client.post("/api/projects", json={"topic_id": ai_topics[0].id}, headers=auth_headers(token))
        resp = client.get("/api/projects/me", headers=auth_headers(token))
        assert resp.status_code == 200

    def test_user_cannot_view_arbitrary_admin_project(self, client, ai_user, cyber_user, ai_topics, cyber_topics, domains):
        """User cannot access another user's project via admin endpoint."""
        t_ai = get_token(client, "aiuser", "userpass123")
        t_cyber = get_token(client, "cyberuser", "userpass123")
        # Cyber user submits project
        r = client.post("/api/projects", json={"topic_id": cyber_topics[0].id}, headers=auth_headers(t_cyber))
        project_id = r.json()["data"]["id"]
        # AI user tries to access it via admin endpoint
        resp = client.get(f"/api/admin/projects/{project_id}", headers=auth_headers(t_ai))
        assert resp.status_code == 403

    def test_user_cannot_view_another_users_reviews_via_admin(self, client, admin_user, ai_user, cyber_user, ai_topics, cyber_topics, domains):
        """A regular user must not access another user's project reviews via admin routes."""
        t_admin = get_token(client, "admin", "adminpass123")
        t_ai = get_token(client, "aiuser", "userpass123")
        t_cyber = get_token(client, "cyberuser", "userpass123")

        r = client.post("/api/projects", json={"topic_id": cyber_topics[0].id}, headers=auth_headers(t_cyber))
        project_id = r.json()["data"]["id"]

        client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Excellent cybersecurity project work.", "status": "PASSED"},
            headers=auth_headers(t_admin),
        )

        # AI user tries to read cyber user's reviews via admin endpoint
        resp = client.get(f"/api/admin/projects/{project_id}/reviews", headers=auth_headers(t_ai))
        assert resp.status_code == 403
