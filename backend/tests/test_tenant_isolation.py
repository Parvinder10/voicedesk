import uuid
import pytest


def test_tenant_isolation_authentication(client):
    suffix = uuid.uuid4().hex[:6]
    # Register Business A (Clinic)
    res_a = client.post("/api/v1/auth/register", json={
        "business_name": f"Lotus Clinic {suffix}",
        "email": f"ayur_{suffix}@lotuscare.com",
        "password": "Password123!",
        "full_name": "Dr. Sunita Sharma",
        "phone": "+919876500001",
        "industry": "clinic"
    })
    assert res_a.status_code == 201, res_a.text
    data_a = res_a.json()
    org_a_id = data_a["organization"]["id"]
    token_a = data_a["token"]["access_token"]

    # Register Business B (Salon)
    res_b = client.post("/api/v1/auth/register", json={
        "business_name": f"Velvet Glow {suffix}",
        "email": f"manager_{suffix}@velvetglow.com",
        "password": "Password123!",
        "full_name": "Rohan Mehra",
        "phone": "+919876500002",
        "industry": "salon"
    })
    assert res_b.status_code == 201, res_b.text
    data_b = res_b.json()
    org_b_id = data_b["organization"]["id"]
    token_b = data_b["token"]["access_token"]

    # Ensure different org IDs
    assert org_a_id != org_b_id

    # Verify User A profile is strictly scoped to Org A
    me_a = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert me_a.status_code == 200
    assert me_a.json()["organization"]["id"] == org_a_id
    assert me_a.json()["organization"]["name"] == f"Lotus Clinic {suffix}"

    # Verify User B profile is strictly scoped to Org B
    me_b = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert me_b.status_code == 200
    assert me_b.json()["organization"]["id"] == org_b_id
    assert me_b.json()["organization"]["name"] == f"Velvet Glow {suffix}"
