"""Comprehensive test suite verifying review persistence, evaluation score stability,
and participant review comments accessibility for Review 1, 2, and 3."""
import pytest
from starlette.testclient import TestClient

from tests.conftest import get_token, auth_headers


class TestReviewPersistenceAndComments:

    def test_full_review_workflow_and_independence(self, client: TestClient, admin_user, ai_user, domains):
        """Test full workflow:
        - Admin evaluates Review 1 with criterion 2=8, criterion 6=7, and comments
        - Verify API returns exact scores 8 and 7, comments, suggestions, is_published=True
        - Verify criterion 2 and 6 do NOT revert to 5
        - Verify participant /api/projects/me/evaluations and /api/projects/me/reviews return exact scores and comments
        - Admin submits Review 2 with independent scores and review notes
        - Verify Review 1 remains completely unchanged and independent
        - Admin submits Review 3 with independent scores and remarks
        - Verify all three rounds are completely independent, accurately totaled, and available to the participant.
        """
        admin_token = get_token(client, "admin", "adminpass123")
        user_token = get_token(client, "aiuser", "userpass123")
        team_id = ai_user.id
        admin_h = auth_headers(admin_token)
        team_h = auth_headers(user_token)

        # ── 1. Submit Review 1 ────────────────────────────────────────────────
        r1_payload = {
            "score_problem_clarity": 8,
            "score_proposed_solution": 9,      # Criterion 2
            "score_solution_quality": 9,
            "score_tech_stack": 7,
            "score_idea_presentation": 6,
            "score_feasibility": 8,
            "score_team_confidence_qa": 7,     # Criterion 6
            "score_confidence_qa": 7,
            "evaluator_name": "Senior Arbiter Minerva",
            "comments": "Outstanding problem statement clarity and architecture.",
            "suggestions": "Focus on backend latency optimizations for Round 2.",
            "suggestions_next_round": "Focus on backend latency optimizations for Round 2.",
            "is_draft": False,
        }

        r1_resp = client.post(f"/api/admin/round-1?team_id={team_id}", json=r1_payload, headers=admin_h)
        assert r1_resp.status_code == 200, f"R1 submit failed: {r1_resp.text}"
        r1_data = r1_resp.json()
        assert r1_data["success"] is True

        # Total for R1: 8 + 9 + 7 + 6 + 8 + 7 = 45 / 60
        expected_r1_total = 8 + 9 + 7 + 6 + 8 + 7
        assert expected_r1_total == 45

        # ── 2. Admin re-opens Review 1 (simulate page refresh / reopen modal) ──
        admin_eval_resp = client.get(f"/api/admin/teams/{team_id}/evaluations", headers=admin_h)
        assert admin_eval_resp.status_code == 200
        admin_eval = admin_eval_resp.json()["data"]

        r1_saved = admin_eval["round_1"]
        assert r1_saved is not None
        assert r1_saved["score_problem_clarity"] == 8
        assert r1_saved["score_solution_quality"] == 9
        assert r1_saved["score_proposed_solution"] == 9  # Must NOT revert to 5!
        assert r1_saved["score_tech_stack"] == 7
        assert r1_saved["score_idea_presentation"] == 6
        assert r1_saved["score_feasibility"] == 8
        assert r1_saved["score_confidence_qa"] == 7
        assert r1_saved["score_team_confidence_qa"] == 7  # Must NOT revert to 5!
        assert r1_saved["total_score"] == 45
        assert r1_saved["comments"] == "Outstanding problem statement clarity and architecture."
        assert r1_saved["suggestions"] == "Focus on backend latency optimizations for Round 2."
        assert r1_saved["suggestions_next_round"] == "Focus on backend latency optimizations for Round 2."
        assert r1_saved["is_published"] is True
        assert r1_saved["status"] == "COMPLETED"

        # ── 3. Participant opens dashboard Review History (Scores Restricted) ───
        team_eval_resp = client.get("/api/projects/me/evaluations", headers=team_h)
        assert team_eval_resp.status_code == 200
        team_eval = team_eval_resp.json()["data"]

        # Scores must be omitted for participants
        assert team_eval.get("scores") is None
        team_r1 = team_eval["round_1"]
        assert team_r1 is not None
        assert team_r1.get("total_score") is None
        assert team_r1.get("score_solution_quality") is None
        assert team_r1.get("score_confidence_qa") is None
        assert team_r1["comments"] == "Outstanding problem statement clarity and architecture."
        assert team_r1["suggestions"] == "Focus on backend latency optimizations for Round 2."
        assert team_r1["status"] == "Completed"

        # Verify participant reviews API matches ParticipantReviewResponse schema
        team_revs_resp = client.get("/api/projects/me/reviews", headers=team_h)
        assert team_revs_resp.status_code == 200
        team_revs = team_revs_resp.json()["data"]
        assert len(team_revs) >= 1
        r1_part = next(r for r in team_revs if (r.get("review_round") == 1 or r.get("round_number") == 1))
        assert r1_part["review_title"] == "REVIEW 1 — PROBLEM & PLAN"
        assert r1_part["status"] == "Completed"
        assert r1_part["evaluator_comments"] == "Outstanding problem statement clarity and architecture."
        assert r1_part["suggested_improvements"] == "Focus on backend latency optimizations for Round 2."
        assert "total_score" not in r1_part
        assert "score" not in r1_part
        assert "admin" not in r1_part

        # Verify participant timeline
        timeline_resp = client.get("/api/projects/me/timeline", headers=team_h)
        assert timeline_resp.status_code == 200
        timeline_events = timeline_resp.json()["data"]
        r1_event = next((e for e in timeline_events if e.get("round_number") == 1 and e.get("event_type") == "REVIEW"), None)
        assert r1_event is not None
        assert r1_event["comments"] == "Outstanding problem statement clarity and architecture."

        # ── 4. Admin submits Review 2 with different scores ────────────────────
        r2_payload = {
            "score_planning_workflow": 9,
            "score_frontend_progress": 8,
            "score_backend_progress": 9,
            "score_prototype_progress": 8,
            "score_technical_quality": 9,
            "score_team_collaboration": 8,
            "score_milestone_completion": 9,
            "evaluator_name": "Senior Arbiter Minerva",
            "review_notes": "Rapid progress across frontend and backend endpoints.",
            "improvement_suggestions": "Complete responsive styling before final review.",
            "is_draft": False,
        }
        r2_resp = client.post(f"/api/admin/round-2?team_id={team_id}", json=r2_payload, headers=admin_h)
        assert r2_resp.status_code == 200

        # Total for R2: 9 + 8 + 9 + 8 + 9 + 8 + 9 = 60 / 70
        expected_r2_total = 60

        # ── 5. Verify Review 1 remains unchanged after Review 2 ───────────────
        admin_eval_after_r2 = client.get(f"/api/admin/teams/{team_id}/evaluations", headers=admin_h).json()["data"]
        r1_check = admin_eval_after_r2["round_1"]
        assert r1_check["score_solution_quality"] == 9
        assert r1_check["score_confidence_qa"] == 7
        assert r1_check["total_score"] == 45
        assert r1_check["comments"] == "Outstanding problem statement clarity and architecture."

        r2_check = admin_eval_after_r2["round_2"]
        assert r2_check["total_score"] == 60
        assert r2_check["review_notes"] == "Rapid progress across frontend and backend endpoints."

        # ── 6. Admin submits Review 3 ─────────────────────────────────────────
        r3_payload = {
            "score_tech_understanding": 10,
            "score_tech_stack_understanding": 10,
            "score_problem_solution_fit": 9,
            "score_innovation_creativity": 9,
            "score_prototype_functionality": 10,
            "score_solution_completeness": 9,
            "score_teamwork_execution": 9,
            "score_qa_handling": 9,
            "evaluator_name": "Chief Arbiter Albus",
            "final_remarks": "Exceptional execution, well-architected solution ready for deployment.",
            "strengths": "Robust security, pristine UX, clean code.",
            "weaknesses": "Minor mobile edge case navigation.",
            "recommendation": "RECOMMENDED_FOR_AWARDS",
            "is_draft": False,
        }
        r3_resp = client.post(f"/api/admin/round-3?team_id={team_id}", json=r3_payload, headers=admin_h)
        assert r3_resp.status_code == 200

        # Total for R3: 10 + 9 + 9 + 10 + 9 + 9 + 9 = 65 / 70
        expected_r3_total = 65

        # Grand total: 45 + 60 + 65 = 170 / 200
        expected_grand_total = 45 + 60 + 65
        assert expected_grand_total == 170

        # ── 7. Verify all three rounds are independently persisted ────────────
        final_eval = client.get(f"/api/admin/teams/{team_id}/evaluations", headers=admin_h).json()["data"]
        assert final_eval["scores"]["r1"] == 45
        assert final_eval["scores"]["r2"] == 60
        assert final_eval["scores"]["r3"] == 65
        assert final_eval["scores"]["grand_total"] == 170
        assert final_eval["scores"]["percentage"] == 85.0

        # Review 1 criteria check
        assert final_eval["round_1"]["score_proposed_solution"] == 9
        assert final_eval["round_1"]["score_team_confidence_qa"] == 7

        # Review 3 criteria check
        assert final_eval["round_3"]["score_tech_stack_understanding"] == 10
        assert final_eval["round_3"]["score_tech_understanding"] == 10
        assert final_eval["round_3"]["recommendation"] == "RECOMMENDED_FOR_AWARDS"

        # ── 8. Verify participant dashboard gets comments & suggestions (no scores)
        final_team_eval = client.get("/api/projects/me/evaluations", headers=team_h).json()["data"]
        assert final_team_eval.get("scores") is None
        assert final_team_eval["round_1"]["comments"] == "Outstanding problem statement clarity and architecture."
        assert final_team_eval["round_2"]["review_notes"] == "Rapid progress across frontend and backend endpoints."
        assert final_team_eval["round_3"]["final_remarks"] == "Exceptional execution, well-architected solution ready for deployment."
        assert final_team_eval["round_3"]["recommendation"] == "RECOMMENDED_FOR_AWARDS"

        final_team_revs = client.get("/api/projects/me/reviews", headers=team_h).json()["data"]
        assert len(final_team_revs) == 3
        for rev in final_team_revs:
            assert "review_round" in rev
            assert "review_title" in rev
            assert "status" in rev
            assert "review_date" in rev
            assert "evaluator_comments" in rev
            assert "suggested_improvements" in rev
            assert "total_score" not in rev
            assert "score" not in rev
            assert "admin" not in rev

    def test_score_validation_strictly_rejects_out_of_range(self, client: TestClient, admin_user, ai_user, domains):
        """Verify scores outside 1-10 are rejected with 422 Unprocessable Entity."""
        admin_token = get_token(client, "admin", "adminpass123")
        team_id = ai_user.id
        admin_h = auth_headers(admin_token)

        # Score < 1 (e.g. 0)
        invalid_r1 = {
            "score_problem_clarity": 0,
            "score_solution_quality": 8,
            "score_tech_stack": 8,
            "score_idea_presentation": 8,
            "score_feasibility": 8,
            "score_confidence_qa": 8,
            "comments": "Test validation",
        }
        res_zero = client.post(f"/api/admin/round-1?team_id={team_id}", json=invalid_r1, headers=admin_h)
        assert res_zero.status_code == 422, f"Expected 422 for score 0, got {res_zero.status_code}"

        # Score > 10 (e.g. 11)
        invalid_r1_high = {
            "score_problem_clarity": 8,
            "score_solution_quality": 11,
            "score_tech_stack": 8,
            "score_idea_presentation": 8,
            "score_feasibility": 8,
            "score_confidence_qa": 8,
            "comments": "Test validation",
        }
        res_high = client.post(f"/api/admin/round-1?team_id={team_id}", json=invalid_r1_high, headers=admin_h)
        assert res_high.status_code == 422, f"Expected 422 for score 11, got {res_high.status_code}"
