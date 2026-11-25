import uuid
import json
from datetime import datetime, date, timedelta, timezone
import pytest


def test_full_inbound_voice_call_lifecycle(client):
    suffix = uuid.uuid4().hex[:6]
    # 1. Business Registration
    reg_res = client.post("/api/v1/auth/register", json={
        "business_name": f"Metropolis Aesthetic Clinic {suffix}",
        "email": f"metro_{suffix}@aesthetic.com",
        "password": "Password123!",
        "full_name": "Dr. Natasha Roy",
        "phone": "+919876599000",
        "industry": "clinic"
    })
    assert reg_res.status_code == 201, reg_res.text
    token = reg_res.json()["token"]["access_token"]
    org_id = reg_res.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add specific service
    s_res = client.post("/api/v1/services", headers=headers, json={
        "name": "HydraFacial Glow Therapy",
        "description": "Multi-step medical grade facial treatment.",
        "duration_minutes": 60,
        "price": 3500.0,
        "currency": "INR"
    })
    assert s_res.status_code == 201
    service_id = s_res.json()["id"]

    # 3. Upload knowledge document
    doc_content = """
    # Metropolis Clinic Service Guide
    HydraFacial Glow Therapy costs 3500 INR and is suitable for all skin types.
    Pre-procedure care: Avoid direct sun exposure 24 hours prior.
    Location: Suite 402, Pinnacle Tower, Bandra West, Mumbai.
    Emergency line: +919876599000.
    """
    files = {
        "file": ("clinic_guide.txt", doc_content.encode("utf-8"), "text/plain")
    }
    upload_res = client.post("/api/v1/knowledge/documents", headers=headers, files=files)
    assert upload_res.status_code == 201

    vapi_call_id = f"vapi_{uuid.uuid4().hex}"
    caller_phone = "+919811223344"

    # 4. Incoming call: Vapi assistant-request
    asst_req = client.post(
        f"/api/v1/vapi/webhook?org_id={org_id}",
        json={
            "message": {
                "type": "assistant-request",
                "call": {
                    "id": vapi_call_id,
                    "metadata": {"organization_id": org_id},
                    "customer": {"number": caller_phone}
                }
            }
        }
    )
    assert asst_req.status_code == 200
    assert "assistant" in asst_req.json()

    # 5. Tool Call 1: identify_customer (caller is new)
    tool_id_req = client.post(
        f"/api/v1/vapi/webhook?org_id={org_id}",
        json={
            "message": {
                "type": "tool-calls",
                "call": {"id": vapi_call_id, "metadata": {"organization_id": org_id}},
                "toolCalls": [
                    {
                        "id": "tc_id",
                        "type": "function",
                        "function": {
                            "name": "identify_customer",
                            "arguments": {"phone": caller_phone}
                        }
                    }
                ]
            }
        }
    )
    assert tool_id_req.status_code == 200
    id_res_parsed = json.loads(tool_id_req.json()["results"][0]["result"])
    assert id_res_parsed["found"] is False

    # 6. Tool Call 2: search_knowledge_base ("How much does HydraFacial cost?")
    tool_rag_req = client.post(
        f"/api/v1/vapi/webhook?org_id={org_id}",
        json={
            "message": {
                "type": "tool-calls",
                "call": {"id": vapi_call_id, "metadata": {"organization_id": org_id}},
                "toolCalls": [
                    {
                        "id": "tc_rag",
                        "type": "function",
                        "function": {
                            "name": "search_knowledge_base",
                            "arguments": {"query": "How much does HydraFacial cost and where is the clinic?"}
                        }
                    }
                ]
            }
        }
    )
    assert tool_rag_req.status_code == 200
    rag_res_parsed = json.loads(tool_rag_req.json()["results"][0]["result"])
    assert rag_res_parsed["has_verified_info"] is True
    assert "3500" in rag_res_parsed["answer"] or "HydraFacial" in rag_res_parsed["answer"]

    # 7. Tool Call 3: check_availability
    future_date = date.today() + timedelta(days=4)
    if future_date.weekday() == 6:
        future_date += timedelta(days=1)

    tool_avail_req = client.post(
        f"/api/v1/vapi/webhook?org_id={org_id}",
        json={
            "message": {
                "type": "tool-calls",
                "call": {"id": vapi_call_id, "metadata": {"organization_id": org_id}},
                "toolCalls": [
                    {
                        "id": "tc_avail",
                        "type": "function",
                        "function": {
                            "name": "check_availability",
                            "arguments": {
                                "service_id": service_id,
                                "date": future_date.isoformat()
                            }
                        }
                    }
                ]
            }
        }
    )
    assert tool_avail_req.status_code == 200
    avail_parsed = json.loads(tool_avail_req.json()["results"][0]["result"])
    assert avail_parsed["available"] is True
    selected_slot = avail_parsed["raw_slots"][0]["start_time"]

    # 8. Tool Call 4: book_appointment
    tool_book_req = client.post(
        f"/api/v1/vapi/webhook?org_id={org_id}",
        json={
            "message": {
                "type": "tool-calls",
                "call": {"id": vapi_call_id, "metadata": {"organization_id": org_id}},
                "toolCalls": [
                    {
                        "id": "tc_book",
                        "type": "function",
                        "function": {
                            "name": "book_appointment",
                            "arguments": {
                                "service_id": service_id,
                                "date_time": selected_slot,
                                "customer_phone": caller_phone,
                                "customer_name": "Meera Kapoor",
                                "notes": "First time HydraFacial treatment"
                            }
                        }
                    }
                ]
            }
        }
    )
    assert tool_book_req.status_code == 200
    book_parsed = json.loads(tool_book_req.json()["results"][0]["result"])
    assert book_parsed["status"] == "confirmed"
    confirmed_appt_id = book_parsed["appointment_id"]

    # 9. Call Ends: end-of-call-report
    report_req = client.post(
        f"/api/v1/vapi/webhook?org_id={org_id}",
        json={
            "message": {
                "type": "end-of-call-report",
                "id": f"evt_end_{uuid.uuid4().hex}",
                "call": {
                    "id": vapi_call_id,
                    "metadata": {"organization_id": org_id},
                    "customer": {"number": caller_phone},
                    "durationSeconds": 182,
                    "cost": 0.24,
                    "recordingUrl": "https://api.vapi.ai/recordings/metro_call.mp3"
                },
                "transcript": "Caller: Hi, how much is HydraFacial?\nAI: HydraFacial is 3500 INR.\nCaller: Great, please book me for Monday.\nAI: Confirmed for Monday at 10 AM.",
                "summary": "Meera Kapoor inquired about HydraFacial pricing and booked an appointment.",
                "analysis": {
                    "structuredData": {
                        "intent": "appointment_booking",
                        "sentiment": "positive"
                    }
                }
            }
        }
    )
    assert report_req.status_code == 200

    # 10. Dashboard & Persistence Verifications:
    # A. Customer profile created
    customers_res = client.get(f"/api/v1/customers?q={caller_phone}", headers=headers)
    assert customers_res.status_code == 200
    assert len(customers_res.json()) == 1
    assert customers_res.json()[0]["name"] == "Meera Kapoor"

    # B. Appointment persisted in Confirmed status
    appt_res = client.get(f"/api/v1/appointments/{confirmed_appt_id}", headers=headers)
    assert appt_res.status_code == 200
    assert appt_res.json()["status"] == "Confirmed"
    assert appt_res.json()["customer_phone"] == caller_phone

    # C. Call record persisted with duration, outcome, and transcript
    calls_res = client.get("/api/v1/calls", headers=headers)
    assert calls_res.status_code == 200
    matching_call = next(c for c in calls_res.json() if c["vapi_call_id"] == vapi_call_id)
    assert matching_call["duration_seconds"] == 182
    assert matching_call["outcome"] == "booked"
    assert matching_call["customer_name"] == "Meera Kapoor"

    transcript_res = client.get(f"/api/v1/calls/{matching_call['id']}/transcript", headers=headers)
    assert transcript_res.status_code == 200
    assert "HydraFacial is 3500 INR" in transcript_res.json()["full_transcript"]
