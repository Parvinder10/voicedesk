import uuid
import json
from datetime import datetime, date, timedelta, timezone
import pytest


def register_vapi_test_org(client):
    suffix = uuid.uuid4().hex[:6]
    res = client.post("/api/v1/auth/register", json={
        "business_name": f"Apex Spine Clinic {suffix}",
        "email": f"apex_{suffix}@spine.com",
        "password": "Password123!",
        "full_name": "Dr. Tarun Verma",
        "phone": "+919876543000",
        "industry": "clinic"
    })
    assert res.status_code == 201, res.text
    token = res.json()["token"]["access_token"]
    org_id = res.json()["organization"]["id"]
    return {"Authorization": f"Bearer {token}"}, org_id


def test_vapi_health(client):
    res = client.get("/api/v1/vapi/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "book_appointment" in data["supported_tools"]


def test_vapi_assistant_request(client):
    headers, org_id = register_vapi_test_org(client)

    payload = {
        "message": {
            "type": "assistant-request",
            "id": f"evt_{uuid.uuid4().hex}",
            "call": {
                "id": f"call_{uuid.uuid4().hex}",
                "metadata": {"organization_id": org_id}
            }
        }
    }

    res = client.post(f"/api/v1/vapi/webhook?org_id={org_id}", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "assistant" in data
    assert "firstMessage" in data["assistant"]


def test_vapi_voice_tool_calls(client):
    headers, org_id = register_vapi_test_org(client)

    # 1. Test get_services tool call
    tool_payload = {
        "message": {
            "type": "tool-calls",
            "id": f"evt_{uuid.uuid4().hex}",
            "call": {
                "id": f"call_{uuid.uuid4().hex}",
                "metadata": {"organization_id": org_id}
            },
            "toolCalls": [
                {
                    "id": "tc_1",
                    "type": "function",
                    "function": {
                        "name": "get_services",
                        "arguments": {}
                    }
                },
                {
                    "id": "tc_2",
                    "type": "function",
                    "function": {
                        "name": "get_business_information",
                        "arguments": {}
                    }
                }
            ]
        }
    }

    res = client.post(f"/api/v1/vapi/webhook?org_id={org_id}", json=tool_payload)
    assert res.status_code == 200, res.text
    results = res.json()["results"]
    assert len(results) == 2
    assert results[0]["toolCallId"] == "tc_1"
    parsed_s = json.loads(results[0]["result"])
    assert "services" in parsed_s

    # 2. Test booking via voice tool call
    future_date = date.today() + timedelta(days=6)
    if future_date.weekday() == 6:
        future_date += timedelta(days=1)
    book_time = datetime(future_date.year, future_date.month, future_date.day, 11, 0, 0, tzinfo=timezone.utc)

    book_tool_payload = {
        "message": {
            "type": "tool-calls",
            "id": f"evt_{uuid.uuid4().hex}",
            "call": {
                "id": f"call_{uuid.uuid4().hex}",
                "metadata": {"organization_id": org_id}
            },
            "toolCalls": [
                {
                    "id": "tc_book_1",
                    "type": "function",
                    "function": {
                        "name": "book_appointment",
                        "arguments": {
                            "date_time": book_time.isoformat(),
                            "customer_phone": "+919876540001",
                            "customer_name": "Rohan Deshmukh",
                            "notes": "Booked via Vapi inbound call."
                        }
                    }
                }
            ]
        }
    }

    book_res = client.post(f"/api/v1/vapi/webhook?org_id={org_id}", json=book_tool_payload)
    assert book_res.status_code == 200, book_res.text
    book_data = json.loads(book_res.json()["results"][0]["result"])
    assert book_data["status"] == "confirmed"
    appt_id = book_data["appointment_id"]

    # 3. Test transfer_to_human tool call
    transfer_payload = {
        "message": {
            "type": "tool-calls",
            "id": f"evt_{uuid.uuid4().hex}",
            "call": {
                "id": f"call_{uuid.uuid4().hex}",
                "metadata": {"organization_id": org_id}
            },
            "toolCalls": [
                {
                    "id": "tc_transfer",
                    "type": "function",
                    "function": {
                        "name": "transfer_to_human",
                        "arguments": {"reason": "Customer requested human supervisor."}
                    }
                }
            ]
        }
    }
    trans_res = client.post(f"/api/v1/vapi/webhook?org_id={org_id}", json=transfer_payload)
    assert trans_res.status_code == 200
    trans_data = json.loads(trans_res.json()["results"][0]["result"])
    assert trans_data["status"] in ["transfer_initiated", "unavailable"]


def test_vapi_end_of_call_report_and_idempotency(client):
    headers, org_id = register_vapi_test_org(client)
    vapi_call_id = f"vapi_call_{uuid.uuid4().hex}"
    event_id = f"evt_report_{uuid.uuid4().hex}"

    end_call_payload = {
        "message": {
            "type": "end-of-call-report",
            "id": event_id,
            "call": {
                "id": vapi_call_id,
                "metadata": {"organization_id": org_id},
                "customer": {"number": "+919876540001"},
                "durationSeconds": 145,
                "cost": 0.18,
                "recordingUrl": "https://api.vapi.ai/recordings/sample.mp3"
            },
            "transcript": "Caller: Hello, I would like to confirm my consultation for tomorrow.\nAI: Your consultation is confirmed for 11 AM.",
            "summary": "Customer called to confirm consultation details.",
            "analysis": {
                "structuredData": {
                    "intent": "appointment_inquiry",
                    "sentiment": "positive"
                }
            }
        }
    }

    # 1. Process end of call report
    res = client.post(f"/api/v1/vapi/webhook?org_id={org_id}", json=end_call_payload)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "call_recorded"

    # 2. Idempotency test: duplicate webhook delivery should be safely ignored
    dup_res = client.post(f"/api/v1/vapi/webhook?org_id={org_id}", json=end_call_payload)
    assert dup_res.status_code == 200
    assert dup_res.json()["status"] == "duplicate_ignored"

    # 3. Retrieve calls list via authenticated API
    calls_res = client.get("/api/v1/calls", headers=headers)
    assert calls_res.status_code == 200
    calls_list = calls_res.json()
    assert len(calls_list) >= 1
    call_record = next(c for c in calls_list if c["vapi_call_id"] == vapi_call_id)
    assert call_record["duration_seconds"] == 145
    assert call_record["outcome"] == "booked"

    # 4. Retrieve call transcript
    transcript_res = client.get(f"/api/v1/calls/{call_record['id']}/transcript", headers=headers)
    assert transcript_res.status_code == 200
    assert "Your consultation is confirmed" in transcript_res.json()["full_transcript"]
