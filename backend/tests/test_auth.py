import uuid
import pytest


def test_register_and_login(client):
    unique_suffix = uuid.uuid4().hex[:6]
    email = f"dr.patel_{unique_suffix}@luminadental.com"
    # 1. Register a new business
    reg_payload = {
        "business_name": f"Lumina Dental Studio {unique_suffix}",
        "email": email,
        "password": "Password123!",
        "full_name": "Dr. Aarav Patel",
        "phone": "+919811122233",
        "industry": "clinic",
        "timezone": "Asia/Kolkata"
    }

    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "token" in data
    assert "user" in data
    assert "organization" in data
    assert data["user"]["email"] == email

    access_token = data["token"]["access_token"]
    refresh_token = data["token"]["refresh_token"]

    # 2. Test /auth/me with access token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["email"] == email

    # 3. Test token refresh
    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert "access_token" in ref_data

    # 4. Test login with correct credentials
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"}
    )
    assert login_res.status_code == 200
    assert "token" in login_res.json()

    # 5. Test login with invalid password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword"}
    )
    assert bad_login.status_code == 401
