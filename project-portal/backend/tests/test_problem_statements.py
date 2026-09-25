"""Tests for official problem statements APIs."""
import pytest
from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum
from tests.conftest import get_token, auth_headers


def test_list_problem_statements_public(client, ai_problem_statements, cyber_problem_statements):
    resp = client.get("/api/problem-statements")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) == 20


def test_filter_by_realm(client, ai_problem_statements, cyber_problem_statements):
    resp_ai = client.get("/api/problem-statements?realm=AI")
    assert resp_ai.status_code == 200
    assert len(resp_ai.json()["data"]) == 10
    assert all(ps["realm"] == "AI" for ps in resp_ai.json()["data"])

    resp_cy = client.get("/api/problem-statements?realm=CYBERSECURITY")
    assert resp_cy.status_code == 200
    assert len(resp_cy.json()["data"]) == 10
    assert all(ps["realm"] == "CYBERSECURITY" for ps in resp_cy.json()["data"])


def test_admin_problem_statement_crud(client, admin_user):
    token = get_token(client, "admin", "adminpass123")
    headers = auth_headers(token)

    # 1. Create problem statement
    payload = {
        "problem_code": "AI-PS-99",
        "realm": "AI",
        "title": "Quantum AI Machine Learning",
        "description": "Full description of quantum challenge.",
        "difficulty": "ADVANCED",
        "status": True,
    }
    resp = client.post("/api/admin/problem-statements", json=payload, headers=headers)
    assert resp.status_code == 201
    ps_data = resp.json()["data"]
    ps_id = ps_data["id"]
    assert ps_data["problem_code"] == "AI-PS-99"

    # 2. Update problem statement
    update_payload = {
        "title": "Updated Quantum AI Challenge",
        "difficulty": "INTERMEDIATE",
    }
    resp_up = client.put(f"/api/admin/problem-statements/{ps_id}", json=update_payload, headers=headers)
    assert resp_up.status_code == 200
    assert resp_up.json()["data"]["title"] == "Updated Quantum AI Challenge"

    # 3. Delete problem statement (unused)
    resp_del = client.delete(f"/api/admin/problem-statements/{ps_id}", headers=headers)
    assert resp_del.status_code == 200
