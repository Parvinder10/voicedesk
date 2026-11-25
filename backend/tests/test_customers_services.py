import uuid
import pytest


def get_auth_token(client):
    suffix = uuid.uuid4().hex[:6]
    res = client.post("/api/v1/auth/register", json={
        "business_name": f"Smile Dental {suffix}",
        "email": f"smile_{suffix}@dental.com",
        "password": "Password123!",
        "full_name": "Dr. Rohit Verma",
        "phone": "+919876543210"
    })
    assert res.status_code == 201, res.text
    return res.json()["token"]["access_token"]


def test_customer_crud_and_duplicate_prevention(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Customer
    res = client.post("/api/v1/customers", headers=headers, json={
        "name": "Ananya Sharma",
        "phone": "+919876512345",
        "email": "ananya@example.com",
        "notes": "Prefers morning appointments."
    })
    assert res.status_code == 201, res.text
    cust_id = res.json()["id"]
    assert res.json()["name"] == "Ananya Sharma"

    # 2. Duplicate phone prevention
    dup_res = client.post("/api/v1/customers", headers=headers, json={
        "name": "Ananya S. Duplicate",
        "phone": "+919876512345"
    })
    assert dup_res.status_code == 409

    # 3. Retrieve customer details
    detail_res = client.get(f"/api/v1/customers/{cust_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["phone"] == "+919876512345"

    # 4. Update customer notes
    patch_res = client.patch(f"/api/v1/customers/{cust_id}", headers=headers, json={
        "notes": "Prefers weekend appointments."
    })
    assert patch_res.status_code == 200
    assert patch_res.json()["notes"] == "Prefers weekend appointments."

    # 5. Search customer
    search_res = client.get("/api/v1/customers?q=Ananya", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1


def test_services_and_staff_crud(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Service
    s_res = client.post("/api/v1/services", headers=headers, json={
        "name": "Teeth Cleaning & Polishing",
        "description": "Deep dental cleaning and stain removal",
        "duration_minutes": 45,
        "price": 1200.0,
        "currency": "INR"
    })
    assert s_res.status_code == 201
    service_id = s_res.json()["id"]

    # 2. List Services
    services_res = client.get("/api/v1/services", headers=headers)
    assert services_res.status_code == 200
    assert any(s["id"] == service_id for s in services_res.json())

    # 3. Create Staff
    st_res = client.post("/api/v1/staff", headers=headers, json={
        "name": "Dr. Kavita Nair",
        "email": "kavita@dental.com",
        "phone": "+919812345678",
        "title": "Periodontist"
    })
    assert st_res.status_code == 201
    staff_id = st_res.json()["id"]

    # 4. List Staff
    staff_list_res = client.get("/api/v1/staff", headers=headers)
    assert staff_list_res.status_code == 200
    assert any(st["id"] == staff_id for st in staff_list_res.json())


def test_business_settings_and_hours(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get settings
    settings_res = client.get("/api/v1/settings", headers=headers)
    assert settings_res.status_code == 200
    assert "business_name" in settings_res.json()

    # 2. Update settings
    update_res = client.patch("/api/v1/settings", headers=headers, json={
        "ai_greeting_en": "Welcome to Smile Dental! How can our dental team help you today?",
        "human_transfer_phone": "+919988776655"
    })
    assert update_res.status_code == 200
    assert update_res.json()["human_transfer_phone"] == "+919988776655"

    # 3. Operating hours
    hours_res = client.get("/api/v1/settings/hours", headers=headers)
    assert hours_res.status_code == 200
    assert len(hours_res.json()) == 7

    # 4. Holidays
    h_res = client.post("/api/v1/settings/holidays", headers=headers, json={
        "name": "Diwali Festival",
        "date": "2026-11-10",
        "is_recurring": False
    })
    assert h_res.status_code == 201
    holiday_id = h_res.json()["id"]

    # Duplicate holiday check
    dup_h = client.post("/api/v1/settings/holidays", headers=headers, json={
        "name": "Diwali Day",
        "date": "2026-11-10"
    })
    assert dup_h.status_code == 409

    # Delete holiday
    del_h = client.delete(f"/api/v1/settings/holidays/{holiday_id}", headers=headers)
    assert del_h.status_code == 200
