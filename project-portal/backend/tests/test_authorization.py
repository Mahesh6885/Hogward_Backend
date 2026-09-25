"""
Critical authorization tests.

Validates that security boundaries are strictly enforced:
- USER cannot access ADMIN endpoints
- USER cannot mutate problem statements (only ADMIN can)
- Realm validation prevents mismatch during registration
- User cannot access another user's project/reviews via admin endpoints
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

    def test_user_cannot_create_problem_statement(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.post(
            "/api/problem-statements",
            json={
                "problem_code": "AI-PS-99",
                "realm": "AI",
                "title": "Rogue Statement",
                "description": "Unauthorized creation",
                "difficulty": "INTERMEDIATE",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    def test_unauthenticated_blocked(self, client):
        assert client.get("/api/admin/dashboard").status_code == 403
        assert client.get("/api/admin/users").status_code == 403
        assert client.get("/api/projects/me").status_code == 403


class TestRealmAccessAndValidation:
    def test_realm_mismatch_prevented_on_team_creation(self, client, admin_user, ai_problem_statements, domains):
        """Registering a CYBERSECURITY realm team with an AI problem statement must fail."""
        token = get_token(client, "admin", "adminpass123")
        ai_ps = ai_problem_statements[0]
        resp = client.post(
            "/api/admin/teams",
            json={
                "team_name": "Mismatch Team",
                "team_leader": "Leader One",
                "username": "mismatch_team",
                "email": "mismatch@example.com",
                "password": "Password123!",
                "realm": "CYBERSECURITY",
                "problem_statement_id": str(ai_ps.id),
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "REALM_MISMATCH"


class TestOwnershipChecks:
    def test_user_can_view_own_project(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        resp = client.get("/api/projects/me", headers=auth_headers(token))
        assert resp.status_code == 200

    def test_user_cannot_view_arbitrary_admin_project(self, client, ai_user, cyber_user, domains):
        """User cannot access another user's project via admin endpoint."""
        t_ai = get_token(client, "aiuser", "userpass123")
        t_cyber = get_token(client, "cyberuser", "userpass123")
        r_cyber = client.get("/api/projects/me", headers=auth_headers(t_cyber))
        project_id = r_cyber.json()["data"]["id"]
        # AI user tries to access it via admin endpoint
        resp = client.get(f"/api/admin/projects/{project_id}", headers=auth_headers(t_ai))
        assert resp.status_code == 403

    def test_user_cannot_view_another_users_reviews_via_admin(self, client, admin_user, ai_user, cyber_user, domains):
        """A regular user must not access another user's project reviews via admin routes."""
        t_admin = get_token(client, "admin", "adminpass123")
        t_ai = get_token(client, "aiuser", "userpass123")
        t_cyber = get_token(client, "cyberuser", "userpass123")

        r_cyber = client.get("/api/projects/me", headers=auth_headers(t_cyber))
        project_id = r_cyber.json()["data"]["id"]

        client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Excellent cybersecurity project work.", "status": "PASSED"},
            headers=auth_headers(t_admin),
        )

        # AI user tries to read cyber user's reviews via admin endpoint
        resp = client.get(f"/api/admin/projects/{project_id}/reviews", headers=auth_headers(t_ai))
        assert resp.status_code == 403
