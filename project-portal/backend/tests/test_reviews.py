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

    def test_multiple_round_reviews_allowed(self, client, admin_user, ai_user, domains):
        project_id, _ = _get_project_id(client, "aiuser", "userpass123")
        token = get_token(client, "admin", "adminpass123")
        r1 = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "First review submission.", "status": "NEEDS_IMPROVEMENT"},
            headers=auth_headers(token),
        )
        assert r1.status_code == 201

        r2 = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json={"round_number": 1, "review_text": "Second review attempt for same round.", "status": "REJECTED"},
            headers=auth_headers(token),
        )
        assert r2.status_code == 201
        assert r2.json()["data"]["status"] == "REJECTED"

        resp = client.get(f"/api/admin/projects/{project_id}/reviews", headers=auth_headers(token))
        assert len(resp.json()["data"]) == 2

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


class TestPhase3ReviewEvaluation:
    """Comprehensive tests for Review 1 (60), Review 2 (70), Review 3 (70) and Live Leaderboard (200)."""

    def test_complete_three_round_evaluation_and_leaderboard(self, client, admin_user, ai_user, domains):
        user_id = ai_user.id
        admin_token = get_token(client, "admin", "adminpass123")
        user_token = get_token(client, "aiuser", "userpass123")

        # ── 1. Round 1 Evaluation (Max 60) ───────────────────────────────────
        r1_payload = {
            "score_problem_clarity": 8,
            "score_proposed_solution": 9,
            "score_tech_stack": 7,
            "score_idea_presentation": 8,
            "score_feasibility": 9,
            "score_team_confidence_qa": 10,
            "evaluator_name": "Chief Arbiter Albus",
            "comments": "Superb understanding of problem statement and viable tech stack.",
            "suggestions_next_round": "Focus on backend architecture and live demo.",
            "is_draft": False,
        }
        resp1 = client.post(
            f"/api/admin/round-1?team_id={user_id}",
            json=r1_payload,
            headers=auth_headers(admin_token),
        )
        assert resp1.status_code == 200, resp1.text
        r1_data = resp1.json()["data"]
        assert r1_data["total_score"] == 51
        assert r1_data["status"] == "COMPLETED"
        assert r1_data["is_locked"] is True

        # Check project advanced to Round 2
        eval_details = client.get(f"/api/admin/teams/{user_id}/evaluations", headers=auth_headers(admin_token)).json()["data"]
        assert eval_details["project"]["current_round"] == 2
        assert eval_details["scores"]["r1"] == 51

        # ── 2. Round 2 Evaluation (Max 70) ───────────────────────────────────
        r2_payload = {
            "score_planning_workflow": 9,
            "score_frontend_progress": 8,
            "score_backend_progress": 9,
            "score_prototype_progress": 8,
            "score_technical_quality": 10,
            "score_team_collaboration": 9,
            "score_milestone_completion": 8,
            "evaluator_name": "Chief Arbiter Albus",
            "review_notes": "Great progress across frontend and backend modules.",
            "improvement_suggestions": "Finalize integration and end-to-end tests.",
            "is_draft": False,
        }
        resp2 = client.post(
            f"/api/admin/round-2?team_id={user_id}",
            json=r2_payload,
            headers=auth_headers(admin_token),
        )
        assert resp2.status_code == 200, resp2.text
        r2_data = resp2.json()["data"]
        assert r2_data["total_score"] == 61
        assert r2_data["status"] == "COMPLETED"

        # Check project advanced to Round 3
        eval_details = client.get(f"/api/admin/teams/{user_id}/evaluations", headers=auth_headers(admin_token)).json()["data"]
        assert eval_details["project"]["current_round"] == 3
        assert eval_details["scores"]["r2"] == 61

        # ── 3. Round 3 Evaluation (Max 70) ───────────────────────────────────
        r3_payload = {
            "score_tech_stack_understanding": 10,
            "score_problem_solution_fit": 9,
            "score_innovation_creativity": 9,
            "score_prototype_functionality": 10,
            "score_solution_completeness": 9,
            "score_teamwork_execution": 10,
            "score_qa_handling": 9,
            "evaluator_name": "Chief Arbiter Albus",
            "final_remarks": "Outstanding solution, flawlessly executed and defended.",
            "strengths": "Architecture, UI, real-time sync.",
            "weaknesses": "None noted.",
            "recommendation": "RECOMMENDED_FOR_AWARDS",
            "is_draft": False,
        }
        resp3 = client.post(
            f"/api/admin/round-3?team_id={user_id}",
            json=r3_payload,
            headers=auth_headers(admin_token),
        )
        assert resp3.status_code == 200, resp3.text
        r3_data = resp3.json()["data"]
        assert r3_data["total_score"] == 66
        assert r3_data["status"] == "COMPLETED"

        # ── 4. Verify Grand Total = 51 + 61 + 66 = 178 / 200 (89.0%) ───────────
        eval_details = client.get(f"/api/admin/teams/{user_id}/evaluations", headers=auth_headers(admin_token)).json()["data"]
        assert eval_details["scores"]["grand_total"] == 178
        assert eval_details["scores"]["percentage"] == 89.0
        assert eval_details["project"]["status"] == "COMPLETED"

        # ── 5. Verify Live Leaderboard and House Cup Gold Podium ─────────────
        lb_resp = client.get("/api/leaderboard", headers=auth_headers(admin_token))
        assert lb_resp.status_code == 200
        lb_data = lb_resp.json()["data"]
        assert lb_data["podium"]["gold"] is not None
        assert lb_data["podium"]["gold"]["team_id"] == user_id
        assert lb_data["podium"]["gold"]["grand_total"] == 178

        # ── 6. Verify User Access to Read-only Evaluations ───────────────────
        user_eval_resp = client.get("/api/projects/me/evaluations", headers=auth_headers(user_token))
        assert user_eval_resp.status_code == 200
        user_eval = user_eval_resp.json()["data"]
        assert user_eval["scores"]["grand_total"] == 178
        assert user_eval["round_1"]["total_score"] == 51
        assert user_eval["round_2"]["total_score"] == 61
        assert user_eval["round_3"]["total_score"] == 66

        # ── 7. Verify User Cannot Submit Evaluations ─────────────────────────
        forbidden_resp = client.post(
            f"/api/admin/round-1?team_id={user_id}",
            json=r1_payload,
            headers=auth_headers(user_token),
        )
        assert forbidden_resp.status_code == 403

        # ── 8. Verify CSV Exports ────────────────────────────────────────────
        lb_csv = client.get("/api/leaderboard/export-csv", headers=auth_headers(admin_token))
        assert lb_csv.status_code == 200
        assert "text/csv" in lb_csv.headers["content-type"]
        assert "Grand Total" in lb_csv.text

        eval_csv = client.get("/api/admin/evaluations/export-csv", headers=auth_headers(admin_token))
        assert eval_csv.status_code == 200
        assert "text/csv" in eval_csv.headers["content-type"]
        assert "Chief Arbiter Albus" in eval_csv.text

