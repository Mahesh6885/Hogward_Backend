"""
Comprehensive Test Suite for Open Innovation Submission and Admin Edit Permissions.
Verifies all 10 scenarios specified in the requirements.
"""
import pytest
from app.models.project import Project, ProjectStatus
from app.models.domain import Domain, DomainName
from app.models.problem_statement import ProblemStatement, RealmEnum
from app.models.user import User


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_token(client, username, password):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["data"]["access_token"]


class TestOpenInnovationWorkflow:

    def test_scenario_1_to_6_oi_registration_draft_and_submission(
        self, client, admin_user, domains
    ):
        admin_token = get_token(client, "admin", "adminpass123")

        # ── 1. Register a new Open Innovation team and verify project remains in DRAFT status
        team_payload = {
            "team_name": "Phoenix Innovation",
            "team_leader": "Harry Potter",
            "username": "phoenix_oi",
            "email": "phoenix@hogwarts.edu",
            "password": "Password123!",
            "domain": "OPEN_INNOVATION",
            "realm": "OPEN_INNOVATION",
            "college_name": "Hogwarts School",
            "organization": "Gryffindor House",
            "department": "Innovation Dept",
            "member_one": "Ron Weasley",
            "member_two": "Hermione Granger",
        }
        create_resp = client.post("/api/admin/teams", json=team_payload, headers=auth_headers(admin_token))
        assert create_resp.status_code == 201, f"Create team failed: {create_resp.text}"
        team_data = create_resp.json()["data"]
        team_id = team_data["id"]

        # Check project initially created is in DRAFT status
        assert team_data["project"] is not None
        assert team_data["project"]["status"] == "DRAFT"
        assert team_data["project"]["is_submitted"] is False

        # ── 2. Log in without entering project details and verify no automatic submission occurs
        oi_token = get_token(client, "phoenix_oi", "Password123!")

        # Hit /api/projects/me (called on dashboard load)
        me_prj_resp = client.get("/api/projects/me", headers=auth_headers(oi_token))
        assert me_prj_resp.status_code == 200
        p_info = me_prj_resp.json()["data"]
        assert p_info["status"] == "DRAFT"
        assert p_info["is_submitted"] is False
        assert p_info["submitted_at"] is None

        # Hit /api/projects/me/evaluations (called on dashboard load, previously auto-submitted!)
        eval_resp = client.get("/api/projects/me/evaluations", headers=auth_headers(oi_token))
        assert eval_resp.status_code == 200

        # Verify still in DRAFT after loading evaluations
        me_prj_check = client.get("/api/projects/me", headers=auth_headers(oi_token))
        assert me_prj_check.json()["data"]["status"] == "DRAFT"
        assert me_prj_check.json()["data"]["is_submitted"] is False

        # ── 3. Save an incomplete draft and confirm status remains DRAFT
        draft_resp = client.patch(
            "/api/projects/me/draft",
            json={
                "project_title": "Magical Plant Growth AI",
                "abstract": "Draft abstract for plant growth tracking.",
            },
            headers=auth_headers(oi_token),
        )
        assert draft_resp.status_code == 200
        draft_data = draft_resp.json()["data"]
        assert draft_data["status"] == "DRAFT"
        assert draft_data["is_submitted"] is False
        assert draft_data["project_title"] == "Magical Plant Growth AI"

        # ── 4. Attempt final submission with missing mandatory fields and verify validation prevents submission
        incomplete_submit = client.post(
            "/api/projects/me/submit",
            json={
                "project_title": "Magical Plant Growth AI",
                "abstract": "Short",  # Missing objectives, solution, technologies, outcome, description, github
            },
            headers=auth_headers(oi_token),
        )
        assert incomplete_submit.status_code == 422
        err_data = incomplete_submit.json()
        assert err_data["error_code"] == "REQUIRED_FIELDS_MISSING"
        assert len(err_data["missing_fields"]) > 0
        # Project should still remain DRAFT in database
        check_still_draft = client.get("/api/projects/me", headers=auth_headers(oi_token))
        assert check_still_draft.json()["data"]["status"] == "DRAFT"
        assert check_still_draft.json()["data"]["is_submitted"] is False

        # ── 5. Complete all mandatory fields and submit the project manually
        complete_submit_payload = {
            "project_title": "Magical Plant Health & Crop Disease Analyzer",
            "problem_statement": "Herbology crops suffer from magical blight diseases that wipe out harvest without early detection.",
            "abstract": "An innovative AI-powered vision system for early detection of magical herbology plant afflictions.",
            "objectives": "1. Collect spectral data on Mandrakes\n2. Train neural classifier with 95% accuracy\n3. Deploy dashboard.",
            "proposed_solution": "Deploy edge cameras with a lightweight CNN model connected to an alert webhook.",
            "technologies": "Python, PyTorch, FastAPI, OpenCV, PostgreSQL",
            "technology_stack": "Python, PyTorch, FastAPI, OpenCV, PostgreSQL",
            "expected_outcome": "Real-time crop anomaly detection and automated alert dispatch to greenhouse staff.",
            "project_description": "Comprehensive implementation details covering data pipeline, camera hardware, and neural inference workflow.",
            "github_url": "https://github.com/hogwarts-open/herbology-blight-ai",
            "demo_url": "https://herbology-ai.demo.hogwarts.edu",
        }
        submit_resp = client.post("/api/projects/me/submit", json=complete_submit_payload, headers=auth_headers(oi_token))
        assert submit_resp.status_code == 201, f"Final submit failed: {submit_resp.text}"
        sub_data = submit_resp.json()["data"]
        assert sub_data["status"] == "SUBMITTED"
        assert sub_data["is_submitted"] is True
        assert sub_data["submitted_at"] is not None
        assert sub_data["project_title"] == "Magical Plant Health & Crop Disease Analyzer"
        assert sub_data["problem_statement_description"] == "Herbology crops suffer from magical blight diseases that wipe out harvest without early detection."

        # ── 6. Confirm that the submitted project becomes non-editable
        locked_draft_resp = client.patch(
            "/api/projects/me/draft",
            json={"abstract": "Trying to edit locked project without permission"},
            headers=auth_headers(oi_token),
        )
        assert locked_draft_resp.status_code == 403

        # Duplicate submission also rejected
        resubmit_attempt = client.post(
            "/api/projects/me/submit",
            json=complete_submit_payload,
            headers=auth_headers(oi_token),
        )
        assert resubmit_attempt.status_code == 409

    def test_scenario_7_to_9_admin_unlock_and_auto_revocation(
        self, client, admin_user, domains
    ):
        admin_token = get_token(client, "admin", "adminpass123")

        # Register Open Innovation team and submit
        team_payload = {
            "team_name": "Ravenclaw Labs",
            "team_leader": "Luna Lovegood",
            "username": "ravenclaw_oi",
            "email": "ravenclaw@hogwarts.edu",
            "password": "Password123!",
            "domain": "OPEN_INNOVATION",
            "realm": "OPEN_INNOVATION",
            "member_one": "Cho Chang",
        }
        c_resp = client.post("/api/admin/teams", json=team_payload, headers=auth_headers(admin_token))
        team_id = c_resp.json()["data"]["id"]
        token = get_token(client, "ravenclaw_oi", "Password123!")

        full_payload = {
            "project_title": "Original Problem Title V1",
            "problem_statement": "Original Problem Statement Description V1 which is long enough to satisfy.",
            "abstract": "Original project abstract with sufficient length.",
            "objectives": "Original objectives breakdown for hackathon submission.",
            "proposed_solution": "Original proposed solution architecture and approach.",
            "technologies": "Python, FastAPI, Svelte",
            "expected_outcome": "Original expected outcome and target metrics.",
            "project_description": "Original detailed project description with multiple sections.",
            "github_url": "https://github.com/ravenclaw/project-v1",
        }
        s_resp = client.post("/api/projects/me/submit", json=full_payload, headers=auth_headers(token))
        assert s_resp.status_code == 201

        # ── 7. Grant Project Details Editing Only (allow_problem_statement_edit=False)
        perm_resp = client.patch(
            f"/api/admin/teams/{team_id}/edit-permission",
            json={"edit_permission": True, "allow_problem_statement_edit": False, "reason": "Fix abstract"},
            headers=auth_headers(admin_token),
        )
        assert perm_resp.status_code == 200
        team_check = perm_resp.json()["data"]
        assert team_check["edit_permission"] is True
        assert team_check["allow_problem_statement_edit"] is False

        # Attempt to modify project details -> Allowed
        p_edit = client.patch(
            "/api/projects/me/draft",
            json={"abstract": "Updated abstract with refined methodology."},
            headers=auth_headers(token),
        )
        assert p_edit.status_code == 200
        assert p_edit.json()["data"]["abstract"] == "Updated abstract with refined methodology."

        # Attempt to modify problem statement description when allow_problem_statement_edit=False -> Protected!
        ps_edit_attempt = client.patch(
            "/api/projects/me/draft",
            json={"problem_statement": "Sneaky unauthorized change to problem statement!"},
            headers=auth_headers(token),
        )
        assert ps_edit_attempt.status_code == 200
        # Problem statement must NOT have changed!
        assert ps_edit_attempt.json()["data"]["problem_statement_description"] == "Original Problem Statement Description V1 which is long enough to satisfy."

        # ── 8. Grant Full Editing Permission including problem statement (allow_problem_statement_edit=True)
        full_perm_resp = client.patch(
            f"/api/admin/teams/{team_id}/edit-permission",
            json={"edit_permission": True, "allow_problem_statement_edit": True, "reason": "Allowed to pivot problem statement"},
            headers=auth_headers(admin_token),
        )
        assert full_perm_resp.status_code == 200
        assert full_perm_resp.json()["data"]["allow_problem_statement_edit"] is True

        # Modify problem statement title and description -> Now allowed!
        ps_update_resp = client.patch(
            "/api/projects/me/draft",
            json={
                "project_title": "Pivoted Problem Title V2",
                "problem_statement": "Pivoted and updated problem statement description with comprehensive scope.",
            },
            headers=auth_headers(token),
        )
        assert ps_update_resp.status_code == 200
        assert ps_update_resp.json()["data"]["project_title"] == "Pivoted Problem Title V2"
        assert ps_update_resp.json()["data"]["problem_statement_description"] == "Pivoted and updated problem statement description with comprehensive scope."

        # ── 9. Resubmit project and verify permissions are automatically revoked
        resubmit_payload = dict(full_payload)
        resubmit_payload["project_title"] = "Pivoted Problem Title V2"
        resubmit_payload["problem_statement"] = "Pivoted and updated problem statement description with comprehensive scope."
        resubmit_payload["abstract"] = "Updated abstract after pivot."

        resub_resp = client.post("/api/projects/me/submit", json=resubmit_payload, headers=auth_headers(token))
        assert resub_resp.status_code == 201

        # Verify permissions automatically revoked
        me_check = client.get("/api/auth/me", headers=auth_headers(token))
        user_info = me_check.json()["data"]
        assert user_info["edit_permission"] is False
        assert user_info["allow_problem_statement_edit"] is False

        # Verify project is locked again
        locked_again = client.patch("/api/projects/me/draft", json={"abstract": "Edit after lock"}, headers=auth_headers(token))
        assert locked_again.status_code == 403

    def test_scenario_10_ai_and_cyber_problem_statements_remain_protected(
        self, client, admin_user, domains, ai_problem_statements
    ):
        admin_token = get_token(client, "admin", "adminpass123")
        ps = ai_problem_statements[0]

        # Register an AI team
        team_payload = {
            "team_name": "Slytherin AI",
            "team_leader": "Draco Malfoy",
            "username": "slytherin_ai",
            "email": "draco@hogwarts.edu",
            "password": "Password123!",
            "domain": "AI",
            "realm": "AI",
            "member_one": "Vincent Crabbe",
            "problem_statement_id": str(ps.id),
        }
        c_resp = client.post("/api/admin/teams", json=team_payload, headers=auth_headers(admin_token))
        team_id = c_resp.json()["data"]["id"]
        token = get_token(client, "slytherin_ai", "Password123!")

        # Submit initial project
        submit_payload = {
            "project_title": "Slytherin Detection Net",
            "abstract": "Valid abstract for AI challenge project.",
            "objectives": "Target objectives for AI problem.",
            "proposed_solution": "Proposed deep learning neural architecture.",
            "technologies": "TensorFlow, FastAPI",
            "expected_outcome": "High classification accuracy.",
            "project_description": "Full description of AI project implementation.",
            "github_url": "https://github.com/slytherin/ai-net",
        }
        s_resp = client.post("/api/projects/me/submit", json=submit_payload, headers=auth_headers(token))
        assert s_resp.status_code == 201
        orig_ps_desc = s_resp.json()["data"]["problem_statement"]["description"]

        # Admin tries to grant allow_problem_statement_edit=True for an AI team
        perm_resp = client.patch(
            f"/api/admin/teams/{team_id}/edit-permission",
            json={"edit_permission": True, "allow_problem_statement_edit": True, "reason": "Edit request"},
            headers=auth_headers(admin_token),
        )
        assert perm_resp.status_code == 200
        # Backend enforces that allow_problem_statement_edit is strictly FALSE for non-OI teams
        assert perm_resp.json()["data"]["allow_problem_statement_edit"] is False
        assert perm_resp.json()["data"]["edit_permission"] is True

        # AI team attempts to overwrite problem statement
        tamper_resp = client.patch(
            "/api/projects/me/draft",
            json={"problem_statement": "Attempting to change official AI problem statement!"},
            headers=auth_headers(token),
        )
        assert tamper_resp.status_code == 200
        # Verify problem statement is still the official one!
        assert tamper_resp.json()["data"]["problem_statement"]["description"] == orig_ps_desc
        assert tamper_resp.json()["data"]["problem_statement_id"] == str(ps.id)
