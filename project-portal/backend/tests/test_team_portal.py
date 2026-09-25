"""Comprehensive tests for Team-Based User Dashboard Enhancement."""
import pytest
from tests.conftest import get_token, auth_headers


class TestTeamPortalFeatures:
    def test_admin_creates_team_with_members(self, client, admin_user, domains):
        admin_token = get_token(client, "admin", "adminpass123")
        payload = {
            "team_name": "Team Alpha",
            "team_leader": "Alice Walker",
            "member_one": "Bob Smith",
            "member_two": "Charlie Brown",
            "member_three": "Diana Prince",
            "college_name": "MIT Institute",
            "department": "Computer Science",
            "academic_year": "2025-2026",
            "username": "team_alpha",
            "email": "alpha@example.com",
            "password": "AlphaPassword123!",
            "phone": "+1-555-0199",
            "domain": "AI",
        }
        resp = client.post("/api/admin/teams", json=payload, headers=auth_headers(admin_token))
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["team_name"] == "Team Alpha"
        assert data["team_leader"] == "Alice Walker"
        assert data["member_one"] == "Bob Smith"
        assert data["member_three"] == "Diana Prince"
        assert data["college_name"] == "MIT Institute"
        assert data["department"] == "Computer Science"
        assert data["academic_year"] == "2025-2026"
        assert data["domain"]["name"] == "AI"

    def test_team_login_and_get_team_details(self, client, admin_user, domains):
        admin_token = get_token(client, "admin", "adminpass123")
        # Create team
        client.post(
            "/api/admin/teams",
            json={
                "team_name": "Cyber Guardians",
                "team_leader": "John Doe",
                "member_one": "Jane Roe",
                "member_two": "Jack Doe",
                "member_three": "Jill Doe",
                "college_name": "Tech University",
                "department": "Cybersecurity",
                "academic_year": "Year 3",
                "username": "cyber_guardians",
                "email": "guardians@example.com",
                "password": "GuardPassword123!",
                "phone": "+1-555-0200",
                "domain": "CYBERSECURITY",
            },
            headers=auth_headers(admin_token),
        )

        # Team logs in
        token = get_token(client, "cyber_guardians", "GuardPassword123!")
        assert token is not None

        # Call GET /api/users/me/team
        resp = client.get("/api/users/me/team", headers=auth_headers(token))
        assert resp.status_code == 200
        team = resp.json()["data"]
        assert team["team_name"] == "Cyber Guardians"
        assert team["team_leader"] == "John Doe"
        assert team["member_one"] == "Jane Roe"
        assert team["college_name"] == "Tech University"
        assert team["domain"]["display_name"] == "Cybersecurity"

    def test_domain_random_topic_locking(self, client, admin_user, domains, ai_topics):
        admin_token = get_token(client, "admin", "adminpass123")
        # Create AI team
        client.post(
            "/api/admin/teams",
            json={
                "team_name": "AI Visionaries",
                "team_leader": "Visi Leader",
                "username": "ai_vision",
                "email": "vision@example.com",
                "password": "VisionPassword123!",
                "domain": "AI",
            },
            headers=auth_headers(admin_token),
        )

        token = get_token(client, "ai_vision", "VisionPassword123!")

        # First call to random topics
        resp1 = client.get("/api/topics/random", headers=auth_headers(token))
        assert resp1.status_code == 200
        topics1 = resp1.json()["data"]
        assert len(topics1) == 10

        # Second call — must return the exact same 10 locked topics (not a new random set)
        resp2 = client.get("/api/topics/random", headers=auth_headers(token))
        assert resp2.status_code == 200
        topics2 = resp2.json()["data"]
        assert [t["id"] for t in topics1] == [t["id"] for t in topics2]

    def test_full_project_submission_and_timeline(self, client, admin_user, domains, ai_topics):
        admin_token = get_token(client, "admin", "adminpass123")
        # Create team
        client.post(
            "/api/admin/teams",
            json={
                "team_name": "Nexus AI",
                "team_leader": "Nexus Leader",
                "username": "nexus_ai",
                "email": "nexus@example.com",
                "password": "NexusPassword123!",
                "domain": "AI",
            },
            headers=auth_headers(admin_token),
        )
        token = get_token(client, "nexus_ai", "NexusPassword123!")

        # Get locked topics
        topics_resp = client.get("/api/topics/random", headers=auth_headers(token))
        selected_topic = topics_resp.json()["data"][0]

        # Submit project with full description fields
        sub_payload = {
            "topic_id": selected_topic["id"],
            "project_title": "Deep Neural Network for Medical Imaging",
            "abstract": "This project develops an automated diagnostics system using deep CNNs.",
            "problem_statement": "Manual scan reading is error-prone and time-consuming.",
            "objectives": "Achieve 98% accuracy on lung cancer classification.",
            "proposed_solution": "Deploy an ensemble of ResNet-50 and EfficientNet models.",
            "technologies": "PyTorch, FastAPI, Docker, PostgreSQL",
            "expected_outcome": "A production web dashboard for radiologists.",
            "project_description": "Detailed project description with multiple paragraphs.\n\nParagraph 2: Methodology.\n\nParagraph 3: Architecture.",
            "github_url": "https://github.com/example/medical-ai",
            "demo_url": "https://demo.example.com",
        }
        sub_resp = client.post("/api/projects", json=sub_payload, headers=auth_headers(token))
        assert sub_resp.status_code == 201
        p_data = sub_resp.json()["data"]
        assert p_data["project_title"] == "Deep Neural Network for Medical Imaging"
        assert p_data["abstract"] == sub_payload["abstract"]
        assert p_data["technologies"] == sub_payload["technologies"]
        assert p_data["status"] == "SUBMITTED"
        project_id = p_data["id"]

        # Team checks /api/projects/me
        my_resp = client.get("/api/projects/me", headers=auth_headers(token))
        assert my_resp.status_code == 200
        assert my_resp.json()["data"]["project_description"] == sub_payload["project_description"]

        # Team checks /api/projects/me/timeline
        tl_resp = client.get("/api/projects/me/timeline", headers=auth_headers(token))
        assert tl_resp.status_code == 200
        tl = tl_resp.json()["data"]
        assert len(tl) >= 1
        assert tl[0]["title"] == "Project Submitted"

        # Admin reviews round 1 with suggested improvements
        rev_payload = {
            "round_number": 1,
            "status": "PASSED",
            "review_text": "Excellent abstract and methodology proposed.",
            "suggested_improvements": "Include ROC curve and latency benchmark in Round 2.",
        }
        rev_resp = client.post(
            f"/api/admin/projects/{project_id}/reviews",
            json=rev_payload,
            headers=auth_headers(admin_token),
        )
        assert rev_resp.status_code == 201
        rev_data = rev_resp.json()["data"]
        assert rev_data["suggested_improvements"] == rev_payload["suggested_improvements"]

        # Team checks reviews
        my_revs = client.get("/api/projects/me/reviews", headers=auth_headers(token))
        assert my_revs.status_code == 200
        assert len(my_revs.json()["data"]) == 1
        assert my_revs.json()["data"][0]["suggested_improvements"] == rev_payload["suggested_improvements"]

        # Team checks timeline again
        tl_resp2 = client.get("/api/projects/me/timeline", headers=auth_headers(token))
        tl2 = tl_resp2.json()["data"]
        assert len(tl2) == 2
        assert tl2[1]["title"] == "Round 1 Review Completed"
        assert tl2[1]["status"] == "PASSED"

    def test_admin_team_management_api(self, client, admin_user, domains):
        admin_token = get_token(client, "admin", "adminpass123")
        # Create team
        client.post(
            "/api/admin/teams",
            json={
                "team_name": "Nexus Alpha",
                "team_leader": "Nexus Alpha Leader",
                "username": "nexus_alpha",
                "email": "nexus_alpha@example.com",
                "password": "Password123!",
                "domain": "AI",
            },
            headers=auth_headers(admin_token),
        )

        # List teams
        list_resp = client.get("/api/admin/teams", headers=auth_headers(admin_token))
        assert list_resp.status_code == 200
        assert "data" in list_resp.json()
        assert "total" in list_resp.json()

        # Filter by search
        search_resp = client.get("/api/admin/teams?search=Nexus", headers=auth_headers(admin_token))
        assert search_resp.status_code == 200
        items = search_resp.json()["data"]
        assert any("Nexus" in (t.get("team_name") or "") for t in items)
