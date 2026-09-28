import pytest
from tests.conftest import get_token, auth_headers

def test_admin_update_team_details(client, admin_user, ai_user, domains):
    admin_token = get_token(client, "admin", "adminpass123")
    user_token = get_token(client, "aiuser", "userpass123")

    # 1. User gets team details initially
    res_before = client.get("/api/users/me/team", headers=auth_headers(user_token))
    assert res_before.status_code == 200

    # 2. Admin updates team details including domain
    update_payload = {
        "team_name": "Updated Gryffindor",
        "name": "Updated Gryffindor",
        "team_leader": "Harry Potter",
        "email": "ai@test.com",
        "phone": "1234567890",
        "college_name": "Hogwarts School",
        "organization": "Hogwarts School",
        "department": "Defense Against Dark Arts",
        "domain": "CYBERSECURITY",
        "status": "ACTIVE",
        "member_one": "Ron Weasley",
        "member_two": "Hermione Granger",
        "member_three": "Neville Longbottom",
    }
    update_res = client.put(
        f"/api/admin/teams/{ai_user.id}",
        json=update_payload,
        headers=auth_headers(admin_token),
    )
    assert update_res.status_code == 200

    # 3. User gets team details again
    res_after = client.get("/api/users/me/team", headers=auth_headers(user_token))
    assert res_after.status_code == 200
    data_after = res_after.json()["data"]

    assert data_after["team_name"] == "Updated Gryffindor"
    assert data_after["team_leader"] == "Harry Potter"
    assert data_after["member_one"] == "Ron Weasley"
    assert data_after["member_two"] == "Hermione Granger"
    assert data_after["member_three"] == "Neville Longbottom"
    assert data_after["college_name"] == "Hogwarts School"
    assert data_after["department"] == "Defense Against Dark Arts"
    assert data_after["domain"]["name"] == "CYBERSECURITY"

    # 4. User's project domain & realm should also be synchronized
    prj_res = client.get("/api/projects/me", headers=auth_headers(user_token))
    assert prj_res.status_code == 200
    prj_data = prj_res.json()["data"]
    assert prj_data["domain"]["name"] == "CYBERSECURITY"
    assert prj_data["realm"] == "CYBERSECURITY"
    assert prj_data["user"]["team_name"] == "Updated Gryffindor"

    # 5. User's assigned problem statement should be in CYBERSECURITY realm
    ps_res = client.get("/api/problem-statements/assigned", headers=auth_headers(user_token))
    assert ps_res.status_code == 200
    ps_data = ps_res.json()["data"]
    assert ps_data["realm"] == "CYBERSECURITY"

    # 6. Admin clears optional fields (member_three, phone) by sending null
    clear_payload = {
        "team_name": "Updated Gryffindor",
        "team_leader": "Harry Potter",
        "email": "ai@test.com",
        "phone": None,
        "college_name": "Hogwarts School",
        "organization": "Hogwarts School",
        "department": "Defense Against Dark Arts",
        "domain": "CYBERSECURITY",
        "status": "ACTIVE",
        "member_one": "Ron Weasley",
        "member_two": "Hermione Granger",
        "member_three": None,
    }
    clear_res = client.put(
        f"/api/admin/teams/{ai_user.id}",
        json=clear_payload,
        headers=auth_headers(admin_token),
    )
    assert clear_res.status_code == 200

    res_cleared = client.get("/api/users/me/team", headers=auth_headers(user_token))
    assert res_cleared.status_code == 200
    data_cleared = res_cleared.json()["data"]
    assert data_cleared["member_three"] is None
    assert data_cleared["phone"] is None
