import pytest
from fastapi import status

def test_register_user_success(client):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "Password123!"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_register_user_duplicate(client):
    # Register first user
    client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "Password123!"}
    )
    # Try duplicate
    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "Password999!"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already registered"

def test_login_success(client):
    # Register
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "Password123!"}
    )
    # Login
    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "Password123!"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_fail(client):
    response = client.post(
        "/auth/login",
        json={"email": "invalid@example.com", "password": "WrongPassword999!"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_token_refresh(client):
    # Register
    reg_response = client.post(
        "/auth/register",
        json={"email": "refresh@example.com", "password": "Password123!"}
    )
    refresh_token = reg_response.json()["refresh_token"]
    
    # Refresh
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == status.HTTP_200_OK
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_get_current_user_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_logout_and_revocation(client):
    # Register/Login
    client.post(
        "/auth/register",
        json={"email": "logout@example.com", "password": "Password123!"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "logout@example.com", "password": "Password123!"}
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Check me endpoint works
    me_response = client.get("/auth/me", headers=headers)
    assert me_response.status_code == status.HTTP_200_OK
    
    # Logout
    logout_response = client.post("/auth/logout", headers=headers)
    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json()["message"] == "Successfully logged out"
    
    # Try me again -> should be unauthorized because of blacklisted token
    me_revoked = client.get("/auth/me", headers=headers)
    assert me_revoked.status_code == status.HTTP_401_UNAUTHORIZED
    assert me_revoked.json()["detail"] == "Token has been revoked"

def test_invalid_tokens_and_refresh(client):
    # Register/Login
    client.post(
        "/auth/register",
        json={"email": "invalid_tokens@example.com", "password": "Password123!"}
    )
    
    # 1. Invalid refresh token type (passing an access token to /auth/refresh)
    login_res = client.post(
        "/auth/login",
        json={"email": "invalid_tokens@example.com", "password": "Password123!"}
    )
    access_token = login_res.json()["access_token"]
    res1 = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert res1.status_code == status.HTTP_401_UNAUTHORIZED
    assert res1.json()["detail"] == "Invalid or expired refresh token"
    
    # 2. Invalid signature or malformed token
    res2 = client.post("/auth/refresh", json={"refresh_token": "malformed.jwt.token"})
    assert res2.status_code == status.HTTP_401_UNAUTHORIZED
    
    # 3. Call /auth/me with invalid token
    me_res = client.get("/auth/me", headers={"Authorization": "Bearer malformed.token"})
    assert me_res.status_code == status.HTTP_401_UNAUTHORIZED

def test_structured_logging():
    import logging
    from backend.core.logging_config import StructuredJSONFormatter, setup_logging
    
    # Instantiating formatter
    formatter = StructuredJSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    
    # Create a mock record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path.py",
        lineno=10,
        msg="Testing logging formatter with password: secret_password and access_token: secret_token",
        args=(),
        exc_info=None
    )
    
    # Add extra context
    record.extra_context = {"extra_key": "extra_val", "password": "should_be_masked"}
    
    formatted = formatter.format(record)
    import json
    parsed = json.loads(formatted)
    
    assert parsed["level"] == "INFO"
    assert parsed["extra_key"] == "extra_val"
    assert parsed["password"] == "[MASKED]"
    assert "secret_password" not in parsed["message"]
    assert "secret_token" not in parsed["message"]
    
    # Call setup_logging
    setup_logging()
