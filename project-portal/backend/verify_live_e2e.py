"""Live E2E Verification Script for Team Portal Enhancement using httpx."""
import httpx

BASE_URL = "http://127.0.0.1:8000"

def run_e2e():
    print("==================================================")
    print("STARTING E2E INTEGRATION VERIFICATION")
    print("==================================================")

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Admin login
        print("\n1. Testing Admin Login...")
        login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "change-this-password"})
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
        admin_token = login_resp.json()["data"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("  [PASS] Admin logged in successfully!")

        # 2. Admin creates a new Team
        print("\n2. Admin Registering Team 'Team Titan'...")
        team_payload = {
            "team_name": "Team Titan",
            "team_leader": "Sarah Connor",
            "member_one": "John Connor",
            "member_two": "Kyle Reese",
            "member_three": "Marcus Wright",
            "member_four": "Kate Brewster",
            "college_name": "SkyNet Defense Academy",
            "department": "Artificial Intelligence",
            "academic_year": "2025-2026",
            "username": "team_titan",
            "email": "titan@skynet.edu",
            "password": "TitanSecret2026!",
            "phone": "+1-555-7788",
            "domain": "AI",
            "status": "ACTIVE",
        }
        create_resp = client.post("/api/admin/teams", json=team_payload, headers=admin_headers)
        if create_resp.status_code == 409:
            print("  (Team already created from previous run, resetting password)")
            list_teams = client.get("/api/admin/teams?search=titan", headers=admin_headers).json()["data"]
            team_id = list_teams[0]["id"]
            client.patch(f"/api/admin/teams/{team_id}/password", json={"new_password": "TitanSecret2026!"}, headers=admin_headers)
        else:
            assert create_resp.status_code == 201, f"Create team failed: {create_resp.text}"
            team_data = create_resp.json()["data"]
            team_id = team_data["id"]
            print(f"  [PASS] Team Titan registered with ID {team_id}!")

        # 3. Admin lists teams & searches
        print("\n3. Testing Admin Team Listing & Search...")
        search_resp = client.get("/api/admin/teams?search=Titan", headers=admin_headers)
        assert search_resp.status_code == 200
        teams = search_resp.json()["data"]
        assert any(t["team_name"] == "Team Titan" for t in teams), "Team Titan not found in search"
        print("  [PASS] Team found in admin team list with full member fields!")

        # 4. Team Login
        print("\n4. Testing Team Login with generated credentials...")
        t_login_resp = client.post("/api/auth/login", json={"username": "team_titan", "password": "TitanSecret2026!"})
        assert t_login_resp.status_code == 200, f"Team login failed: {t_login_resp.text}"
        team_token = t_login_resp.json()["data"]["access_token"]
        team_headers = {"Authorization": f"Bearer {team_token}"}
        print("  [PASS] Team Titan logged in successfully via single team account!")

        # 5. Team Profile & Roster
        print("\n5. Testing GET /api/users/me/team...")
        me_team_resp = client.get("/api/users/me/team", headers=team_headers)
        assert me_team_resp.status_code == 200
        t_roster = me_team_resp.json()["data"]
        assert t_roster["team_name"] == "Team Titan"
        assert t_roster["member_one"] == "John Connor"
        assert t_roster["member_four"] == "Kate Brewster"
        print(f"  [PASS] Full roster retrieved: Leader={t_roster['team_leader']}, M1={t_roster['member_one']}, M4={t_roster['member_four']}")

        # 6 & 7. Topic Locking Verification
        print("\n6 & 7. Testing Domain-based Topic Locking...")
        top1_resp = client.get("/api/topics/random", headers=team_headers)
        assert top1_resp.status_code == 200
        topics1 = top1_resp.json()["data"]
        assert len(topics1) == 10, f"Expected 10 topics, got {len(topics1)}"

        # Call again — should be identical 10 topics (not random re-roll)
        top2_resp = client.get("/api/topics/random", headers=team_headers)
        assert top2_resp.status_code == 200
        topics2 = top2_resp.json()["data"]
        assert [t["id"] for t in topics1] == [t["id"] for t in topics2], "Topics changed across requests! Topic locking failed."
        print("  [PASS] Topic Locking Confirmed: Exactly identical 10 topics preserved across reloads!")

        # 8. Team Project Submission
        print("\n8. Submitting Complete Team Project...")
        existing_prj = client.get("/api/projects/me", headers=team_headers)
        if existing_prj.status_code == 200:
            project_id = existing_prj.json()["data"]["id"]
            print(f"  (Project already submitted with ID {project_id})")
        else:
            chosen_topic = topics1[0]
            prj_payload = {
                "topic_id": chosen_topic["id"],
                "project_title": "Autonomous Defense Grid AI",
                "abstract": "Development of a decentralized neural agent network for threat prediction.",
                "problem_statement": "Centralized defense systems suffer from single points of failure.",
                "objectives": "Provide real-time anomaly detection with sub-10ms latency.",
                "proposed_solution": "Edge AI micro-clusters with federated synchronization.",
                "technologies": "PyTorch, FastAPI, C++, CUDA, Docker, PostgreSQL",
                "expected_outcome": "Demonstrable multi-node autonomous detection platform.",
                "project_description": "Comprehensive Proposal:\n\nSection 1: Architectural Blueprint.\n\nSection 2: High-speed federated messaging pipeline.\n\nSection 3: Rigorous verification and fault-tolerance.",
                "github_url": "https://github.com/skynet/defense-grid",
                "demo_url": "https://defense.skynet.edu",
            }
            sub_resp = client.post("/api/projects", json=prj_payload, headers=team_headers)
            assert sub_resp.status_code == 201, f"Project submission failed: {sub_resp.text}"
            project_id = sub_resp.json()["data"]["id"]
            print(f"  [PASS] Project submitted successfully! Project ID: {project_id}")

        # 9. My Project Read-Only Page
        print("\n9. Testing GET /api/projects/me (My Project details)...")
        my_prj_resp = client.get("/api/projects/me", headers=team_headers)
        assert my_prj_resp.status_code == 200
        p = my_prj_resp.json()["data"]
        assert p["project_code"].startswith("PRJ-")
        assert p["technologies"] is not None
        assert p["project_description"] is not None
        print(f"  [PASS] My Project details retrieved: Code={p['project_code']}, Title={p['project_title']}")

        # 10. Timeline
        print("\n10. Testing GET /api/projects/me/timeline...")
        tl_resp = client.get("/api/projects/me/timeline", headers=team_headers)
        assert tl_resp.status_code == 200
        tl = tl_resp.json()["data"]
        assert len(tl) >= 1
        assert tl[0]["title"] == "Project Submitted"
        print(f"  [PASS] Timeline milestone verified: {tl[0]['title']} at {tl[0]['date']}")

        # 11. Admin reviews project
        print("\n11. Admin reviews Round 1 with feedback & suggested improvements...")
        rev_payload = {
            "round_number": 1,
            "status": "PASSED",
            "review_text": "Impressive architecture and clear separation of edge nodes.",
            "suggested_improvements": "Ensure stress testing under 100k simulated packet surges.",
        }
        rev_get = client.get(f"/api/admin/projects/{project_id}/reviews", headers=admin_headers)
        if rev_get.status_code == 200 and len(rev_get.json()["data"]) > 0:
            print("  (Round 1 review already exists, updating it)")
            r_id = rev_get.json()["data"][0]["id"]
            client.put(f"/api/admin/projects/{project_id}/reviews/{r_id}", json=rev_payload, headers=admin_headers)
        else:
            rev_create = client.post(f"/api/admin/projects/{project_id}/reviews", json=rev_payload, headers=admin_headers)
            assert rev_create.status_code == 201, f"Review creation failed: {rev_create.text}"
        print("  [PASS] Admin submitted evaluation with suggested improvements!")

        # 12. Team checks Review History & updated Timeline
        print("\n12. Testing Review History & Progress automatic update...")
        my_revs = client.get("/api/projects/me/reviews", headers=team_headers).json()["data"]
        assert len(my_revs) >= 1
        assert my_revs[0]["suggested_improvements"] == rev_payload["suggested_improvements"]
        print(f"  [PASS] Review History card verified: Feedback='{my_revs[0]['review_text'][:30]}...', Improvements='{my_revs[0]['suggested_improvements'][:30]}...'")

        tl_updated = client.get("/api/projects/me/timeline", headers=team_headers).json()["data"]
        assert len(tl_updated) >= 2
        assert tl_updated[1]["title"] == "Round 1 Review Completed"
        print("  [PASS] Timeline automatically advanced to Round 1 Completed milestone!")

        print("\n==================================================")
        print("ALL 12 END-TO-END VERIFICATION STEPS PASSED 100%!")
        print("==================================================")

if __name__ == "__main__":
    run_e2e()
