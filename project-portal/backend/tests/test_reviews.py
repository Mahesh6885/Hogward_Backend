"""Tests for review creation, update, and access control."""
import pytest
from tests.conftest import get_token, auth_headers


def _get_project_id(client, username, password):
    token = get_token(client, username, password)
    r = client.get("/api/projects/me", headers=auth_headers(token))
    assert r.status_code == 200, r.text
    return r.json()["data"]["id"], token


class TestCreateReview:
    def test_admin_creates_review(self, client, admin_user, ai_user, domains):
        project_id, _ = _get_project_id(client, "aiuser", "userpass123")
        token = get_token(client, "admin", "adminpass123")
        resp = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Good project direction indeed.", "status": "PASSED"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["round_number"] == 1
        assert data["status"] == "PASSED"

    def test_normal_user_cannot_create_review(self, client, ai_user, domains):
        token = get_token(client, "aiuser", "userpass123")
        project_id, _ = _get_project_id(client, "aiuser", "userpass123")
        # re-login as same user
        resp = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "I am reviewing myself!", "status": "PASSED"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    def test_review_round_validation(self, client, admin_user, ai_user, domains):
        """Cannot skip rounds — project must be at the round being reviewed."""
        project_id, _ = _get_project_id(client, "aiuser", "userpass123")
        token = get_token(client, "admin", "adminpass123")
        resp = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 2, "review_text": "Skipping to round 2 illegally!", "status": "PASSED"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 400
        assert "round" in resp.json()["message"].lower()

    def test_duplicate_round_review_prevented(self, client, admin_user, ai_user, domains):
        project_id, _ = _get_project_id(client, "aiuser", "userpass123")
        token = get_token(client, "admin", "adminpass123")
        client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "First review submission.", "status": "PASSED"},
            headers=auth_headers(token),
        )
        resp = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Duplicate review attempt.", "status": "NEEDS_IMPROVEMENT"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 409

    def test_review_advances_round_on_pass(self, client, admin_user, ai_user, domains):
        project_id, user_token = _get_project_id(client, "aiuser", "userpass123")
        admin_token = get_token(client, "admin", "adminpass123")

        # Round 1 → PASSED → project moves to round 2
        client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Round 1 passed successfully.", "status": "PASSED"},
            headers=auth_headers(admin_token),
        )

        project_resp = client.get(f"/api/admin/projects/{project_id}", headers=auth_headers(admin_token))
        assert project_resp.json()["data"]["current_round"] == 2

    def test_all_rounds_preserved(self, client, admin_user, ai_user, domains):
        """All review rounds must remain in the database — never overwritten."""
        project_id, user_token = _get_project_id(client, "aiuser", "userpass123")
        admin_token = get_token(client, "admin", "adminpass123")

        client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Round 1 review text here.", "status": "PASSED"},
            headers=auth_headers(admin_token),
        )
        client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 2, "review_text": "Round 2 review needs more work.", "status": "NEEDS_IMPROVEMENT"},
            headers=auth_headers(admin_token),
        )

        resp = client.get(f"/api/admin/projects/{project_id}/reviews", headers=auth_headers(admin_token))
        reviews = resp.json()["data"]
        assert len(reviews) == 2
        assert reviews[0]["round_number"] == 1
        assert reviews[1]["round_number"] == 2

    def test_user_can_view_own_reviews(self, client, admin_user, ai_user, domains):
        project_id, user_token = _get_project_id(client, "aiuser", "userpass123")
        admin_token = get_token(client, "admin", "adminpass123")
        client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Your project looks good so far.", "status": "PASSED"},
            headers=auth_headers(admin_token),
        )
        resp = client.get("/api/projects/me/reviews", headers=auth_headers(user_token))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1


class TestUpdateReview:
    def test_admin_updates_review(self, client, admin_user, ai_user, domains):
        project_id, _ = _get_project_id(client, "aiuser", "userpass123")
        admin_token = get_token(client, "admin", "adminpass123")
        create_resp = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Initial review text here.", "status": "PENDING"},
            headers=auth_headers(admin_token),
        )
        review_id = create_resp.json()["data"]["id"]
        update_resp = client.put(
            f"/api/admin/projects/{project_id}/reviews/{review_id}",
            json={"review_text": "Updated review text.", "status": "PASSED"},
            headers=auth_headers(admin_token),
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["status"] == "PASSED"
        assert update_resp.json()["data"]["review_text"] == "Updated review text."

    def test_admin_updates_review_to_rejected(self, client, admin_user, ai_user, domains):
        project_id, _ = _get_project_id(client, "aiuser", "userpass123")
        admin_token = get_token(client, "admin", "adminpass123")
        create_resp = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Initial review pending.", "status": "IN_REVIEW"},
            headers=auth_headers(admin_token),
        )
        review_id = create_resp.json()["data"]["id"]

        update_resp = client.put(
            f"/api/admin/projects/{project_id}/reviews/{review_id}",
            json={"review_text": "Project failed criteria and is rejected.", "status": "REJECTED"},
            headers=auth_headers(admin_token),
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["status"] == "REJECTED"

        # Verify project status updated to REJECTED
        proj_resp = client.get(f"/api/admin/projects/{project_id}", headers=auth_headers(admin_token))
        assert proj_resp.json()["data"]["status"] == "REJECTED"

    def test_admin_post_review_with_upsert(self, client, admin_user, ai_user, domains):
        project_id, _ = _get_project_id(client, "aiuser", "userpass123")
        admin_token = get_token(client, "admin", "adminpass123")
        client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "First review text.", "status": "IN_REVIEW"},
            headers=auth_headers(admin_token),
        )

        # Upsert=true should update existing review instead of 409
        upsert_resp = client.post(
            f"/api/admin/projects/{project_id}/reviews?upsert=true",
            json={"round_number": 1, "review_text": "Overwritten review text.", "status": "REJECTED"},
            headers=auth_headers(admin_token),
        )
        assert upsert_resp.status_code == 201
        assert upsert_resp.json()["data"]["status"] == "REJECTED"
        assert upsert_resp.json()["data"]["review_text"] == "Overwritten review text."
