import uuid
from datetime import datetime, date, timedelta, timezone
import pytest


def setup_org_and_service(client):
    suffix = uuid.uuid4().hex[:6]
    res = client.post("/api/v1/auth/register", json={
        "business_name": f"Aura Wellness Clinic {suffix}",
        "email": f"aura_{suffix}@clinic.com",
        "password": "Password123!",
        "full_name": "Dr. Sameer Khan",
        "phone": "+919876543211",
        "industry": "clinic"
    })
    assert res.status_code == 201, res.text
    token = res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch default service created on registration
    services_res = client.get("/api/v1/services", headers=headers)
    assert services_res.status_code == 200
    service_id = services_res.json()[0]["id"]

    # Fetch staff
    staff_res = client.get("/api/v1/staff", headers=headers)
    assert staff_res.status_code == 200
    staff_id = staff_res.json()[0]["id"]

    return headers, service_id, staff_id


def test_availability_calculation(client):
    headers, service_id, staff_id = setup_org_and_service(client)

    # Pick a date 3 days in the future (a weekday)
    target_date = (date.today() + timedelta(days=3))
    # If it falls on Sunday, push to Monday
    if target_date.weekday() == 6:
        target_date += timedelta(days=1)

    res = client.get(
        f"/api/v1/availability?service_id={service_id}&date={target_date.isoformat()}",
        headers=headers
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["service_id"] == service_id
    assert data["is_available"] is True
    assert len(data["available_slots"]) > 0

    first_slot = data["available_slots"][0]
    assert "start_time" in first_slot
    assert "end_time" in first_slot
    assert "formatted_time" in first_slot


def test_booking_and_double_booking_prevention(client):
    headers, service_id, staff_id = setup_org_and_service(client)

    # Choose appointment start time 5 days in future at 10:00 AM UTC
    future_date = date.today() + timedelta(days=5)
    if future_date.weekday() == 6:
        future_date += timedelta(days=1)
    
    start_time = datetime(future_date.year, future_date.month, future_date.day, 10, 0, 0, tzinfo=timezone.utc)

    # 1. Book initial appointment
    book_res = client.post("/api/v1/appointments", headers=headers, json={
        "service_id": service_id,
        "customer_phone": "+919876599999",
        "customer_name": "Vikram Seth",
        "staff_id": staff_id,
        "start_time": start_time.isoformat(),
        "notes": "First checkup."
    })
    assert book_res.status_code == 201, book_res.text
    appt_data = book_res.json()
    appt_id = appt_data["id"]
    assert appt_data["status"] == "Confirmed"
    assert appt_data["customer_name"] == "Vikram Seth"

    # 2. Attempt double booking on identical slot for the same staff
    dup_res = client.post("/api/v1/appointments", headers=headers, json={
        "service_id": service_id,
        "customer_phone": "+919876588888",
        "customer_name": "Pooja Hegde",
        "staff_id": staff_id,
        "start_time": start_time.isoformat()
    })
    assert dup_res.status_code == 409
    assert "Double-booking prevented" in dup_res.json()["detail"]

    # 3. Reschedule the appointment to 2 hours later
    new_start = start_time + timedelta(hours=2)
    resched_res = client.post(
        f"/api/v1/appointments/{appt_id}/reschedule",
        headers=headers,
        json={
            "new_start_time": new_start.isoformat(),
            "reason": "Customer had a scheduling conflict."
        }
    )
    assert resched_res.status_code == 200, resched_res.text
    resched_data = resched_res.json()
    assert resched_data["status"] == "Rescheduled"

    # 4. Now the original slot should be free to book!
    rebook_res = client.post("/api/v1/appointments", headers=headers, json={
        "service_id": service_id,
        "customer_phone": "+919876588888",
        "customer_name": "Pooja Hegde",
        "staff_id": staff_id,
        "start_time": start_time.isoformat()
    })
    assert rebook_res.status_code == 201, rebook_res.text

    # 5. Cancel the appointment
    cancel_res = client.post(
        f"/api/v1/appointments/{appt_id}/cancel",
        headers=headers,
        json={"reason": "Patient is out of town."}
    )
    assert cancel_res.status_code == 200, cancel_res.text
    assert cancel_res.json()["status"] == "Cancelled"
    assert cancel_res.json()["cancellation_reason"] == "Patient is out of town."
