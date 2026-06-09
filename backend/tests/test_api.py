import pytest
from fastapi import status

@pytest.fixture
def auth_headers(client):
    # Setup user and return auth headers
    client.post(
        "/auth/register",
        json={"email": "api_test@example.com", "password": "Password123!"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "api_test@example.com", "password": "Password123!"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_submit_calculator_and_recommendations(client, auth_headers):
    # Submit carbon questionnaire
    response = client.post(
        "/calculator/submit",
        json={
            "transportation_car": 500,
            "transportation_bike": 20,
            "transportation_public": 100,
            "transportation_flights": 1000,
            "energy_electricity: ": 150,
            "energy_ac": 40,
            "energy_appliance": 20,
            "food_preference": "non-vegetarian",
            "shopping_clothing": 5,
            "shopping_electronics": 2,
            "waste_recycling": "rarely",
            "waste_plastic": "high"
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["total_emissions"] > 0
    assert data["user_id"] is not None
    
    # Get generated recommendations
    rec_response = client.get("/recommendations/", headers=auth_headers)
    assert rec_response.status_code == status.HTTP_200_OK
    recs = rec_response.json()
    assert len(recs) > 0
    
    # Toggle recommendation completion
    rec_id = recs[0]["id"]
    patch_response = client.patch(f"/recommendations/{rec_id}/complete", headers=auth_headers)
    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.json()["is_completed"] is True

def test_challenges_flow(client, auth_headers):
    # Get all challenges
    list_response = client.get("/challenges/", headers=auth_headers)
    assert list_response.status_code == status.HTTP_200_OK
    challenges = list_response.json()
    assert len(challenges) > 0
    
    # Join challenge
    challenge_id = challenges[0]["id"]
    join_response = client.post(
        "/challenges/join",
        json={"challenge_id": challenge_id},
        headers=auth_headers
    )
    assert join_response.status_code == status.HTTP_201_CREATED
    progress = join_response.json()
    assert progress["completion_status"] == "in_progress"
    
    # Complete challenge
    prog_id = progress["id"]
    comp_response = client.post(
        f"/challenges/{prog_id}/complete",
        headers=auth_headers
    )
    assert comp_response.status_code == status.HTTP_200_OK
    assert comp_response.json()["completion_status"] == "completed"
    assert comp_response.json()["points_earned"] > 0

def test_analytics(client, auth_headers):
    # Verify summary endpoint works
    summary_response = client.get("/analytics/summary", headers=auth_headers)
    assert summary_response.status_code == status.HTTP_200_OK
    summary_data = summary_response.json()
    assert "current_month_emissions" in summary_data
    assert "sustainability_score" in summary_data
    
    # Verify history endpoint works
    history_response = client.get("/analytics/history", headers=auth_headers)
    assert history_response.status_code == status.HTTP_200_OK
    history_data = history_response.json()
    assert "trends" in history_data

def test_analytics_with_entries(client, auth_headers):
    # 1. Submit first entry (large emissions for penalty)
    res1 = client.post(
        "/calculator/submit",
        json={
            "transportation_car": 1200,
            "transportation_bike": 0,
            "transportation_public": 0,
            "transportation_flights": 0,
            "energy_electricity": 100,
            "energy_ac": 0,
            "energy_appliance": 0,
            "food_preference": "non-vegetarian",
            "shopping_clothing": 0,
            "shopping_electronics": 0,
            "waste_recycling": "rarely",
            "waste_plastic": "high"
        },
        headers=auth_headers
    )
    assert res1.status_code == status.HTTP_201_CREATED
    
    # 2. Join a challenge and complete it to boost score
    list_res = client.get("/challenges/", headers=auth_headers)
    challenge_id = list_res.json()[0]["id"]
    join_res = client.post(
        "/challenges/join",
        json={"challenge_id": challenge_id},
        headers=auth_headers
    )
    prog_id = join_res.json()["id"]
    client.post(f"/challenges/{prog_id}/complete", headers=auth_headers)
    
    # 3. Complete a recommendation
    recs = client.get("/recommendations/", headers=auth_headers).json()
    rec_id = recs[0]["id"]
    client.patch(f"/recommendations/{rec_id}/complete", headers=auth_headers)
    
    # 4. Submit second entry (current month)
    res2 = client.post(
        "/calculator/submit",
        json={
            "transportation_car": 100,
            "transportation_bike": 0,
            "transportation_public": 0,
            "transportation_flights": 0,
            "energy_electricity": 20,
            "energy_ac": 0,
            "energy_appliance": 0,
            "food_preference": "vegan",
            "shopping_clothing": 0,
            "shopping_electronics": 0,
            "waste_recycling": "always",
            "waste_plastic": "low"
        },
        headers=auth_headers
    )
    assert res2.status_code == status.HTTP_201_CREATED
    
    # Check analytics summary with entries
    summary_response = client.get("/analytics/summary", headers=auth_headers)
    assert summary_response.status_code == status.HTTP_200_OK
    data = summary_response.json()
    assert data["current_month_emissions"] > 0
    assert data["previous_month_emissions"] > 0
    assert data["reduction_percentage"] > 0
    assert data["sustainability_score"] > 0
    
    # Check analytics history
    history_response = client.get("/analytics/history", headers=auth_headers)
    assert history_response.status_code == status.HTTP_200_OK
    assert len(history_response.json()["trends"]) >= 2

def test_validation_error_middleware(client, auth_headers):
    # Invalid submission to trigger request validation exception
    response = client.post(
        "/calculator/submit",
        json={
            "transportation_car": -500
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["title"] == "Validation Error"
    assert "errors" in data

def test_error_handlers_directly():
    import asyncio
    from starlette.requests import Request
    from sqlalchemy.exc import SQLAlchemyError
    from backend.middleware.errors import global_exception_handler, database_exception_handler
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test-error",
        "headers": [],
    }
    req = Request(scope)
    
    res_global = asyncio.run(global_exception_handler(req, Exception("Test generic error")))
    assert res_global.status_code == 500
    
    res_db = asyncio.run(database_exception_handler(req, SQLAlchemyError("Test DB error")))
    assert res_db.status_code == 500
