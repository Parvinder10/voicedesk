import uuid
import pytest


def test_dashboard_overview_and_activity(client):
    suffix = uuid.uuid4().hex[:6]
    reg_res = client.post("/api/v1/auth/register", json={
        "business_name": f"Analytics Test Spa {suffix}",
        "email": f"spa_{suffix}@analytics.com",
        "password": "Password123!",
        "full_name": "Kavita Rao",
        "phone": "+919876548888"
    })
    assert reg_res.status_code == 201, reg_res.text
    token = reg_res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch overview
    ov_res = client.get("/api/v1/dashboard/overview", headers=headers)
    assert ov_res.status_code == 200
    ov_data = ov_res.json()
    assert "metrics" in ov_data
    assert "outcomes_breakdown" in ov_data
    assert "peak_calling_hours" in ov_data
    assert "resolution_rate_percentage" in ov_data["metrics"]

    # 2. Fetch activity stream
    act_res = client.get("/api/v1/dashboard/activity", headers=headers)
    assert act_res.status_code == 200
    assert isinstance(act_res.json(), list)
