import json
import logging
import uuid
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import (
    Organization, BusinessSettings, BusinessHours, Service, Staff,
    Customer, Appointment, Call, CallTranscript, CallSummary,
    WebhookEvent, AuditLog
)
from app.schemas.appointment import AppointmentCreate, AppointmentReschedule, AppointmentCancel
from app.services.availability_service import AvailabilityService
from app.services.appointment_service import AppointmentService
from app.services.rag_service import RAGService
from app.api.v1.customers import normalize_phone

logger = logging.getLogger("voicedesk.vapi")


class VapiService:
    @staticmethod
    def resolve_organization(
        db: Session,
        call_obj: Optional[Dict[str, Any]],
        org_id_param: Optional[str] = None
    ) -> Optional[Organization]:
        """Resolves target Organization securely from authenticated metadata or phone mappings."""
        if org_id_param:
            org = db.query(Organization).filter_by(id=org_id_param).first()
            if org:
                return org

        if not call_obj:
            return db.query(Organization).first()

        metadata = call_obj.get("metadata") or {}
        if "organization_id" in metadata:
            org = db.query(Organization).filter_by(id=metadata["organization_id"]).first()
            if org:
                return org

        # Match by assistant ID
        assistant_id = call_obj.get("assistantId")
        if assistant_id:
            settings = db.query(BusinessSettings).filter_by(vapi_assistant_id=assistant_id).first()
            if settings:
                return db.query(Organization).filter_by(id=settings.organization_id).first()

        # Match by recipient phone number
        phone_number_obj = call_obj.get("phoneNumber") or {}
        to_number = phone_number_obj.get("number")
        if to_number:
            org = db.query(Organization).filter_by(phone=to_number).first()
            if org:
                return org

        # Default fallback to first organization
        return db.query(Organization).first()

    @classmethod
    def execute_tool(
        cls,
        db: Session,
        org: Organization,
        tool_name: str,
        args: Dict[str, Any],
        call_id_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes verified voice receptionist tools with input validation,
        tenant scoping, business rule enforcement, and structured results.
        """
        logger.info(f"Executing voice tool: {tool_name} for Org: {org.name}")

        try:
            # 1. identify_customer
            if tool_name == "identify_customer":
                phone_raw = args.get("phone", "")
                if not phone_raw:
                    return {"status": "error", "message": "Phone number is required."}
                phone = normalize_phone(phone_raw)
                customer = db.query(Customer).filter_by(organization_id=org.id, phone=phone).first()
                if not customer:
                    return {
                        "found": False,
                        "phone": phone,
                        "message": "No existing customer found with this phone number. Ask if they are a new customer."
                    }
                # Fetch recent appointments
                recent_appts = db.query(Appointment).filter_by(
                    organization_id=org.id,
                    customer_id=customer.id
                ).order_by(Appointment.start_time.desc()).limit(3).all()

                appts_data = [
                    {
                        "id": a.id,
                        "service": a.service.name if a.service else "Service",
                        "start_time": a.start_time.isoformat(),
                        "status": a.status
                    }
                    for a in recent_appts
                ]
                return {
                    "found": True,
                    "customer_id": customer.id,
                    "name": customer.name,
                    "phone": customer.phone,
                    "notes": customer.notes,
                    "recent_appointments": appts_data
                }

            # 2. create_customer
            elif tool_name == "create_customer":
                phone = normalize_phone(args.get("phone", ""))
                name = args.get("name", "").strip()
                if not phone or not name:
                    return {"status": "error", "message": "Both name and phone are required."}
                existing = db.query(Customer).filter_by(organization_id=org.id, phone=phone).first()
                if existing:
                    existing.name = name
                    if args.get("email"):
                        existing.email = args.get("email")
                    db.commit()
                    return {"status": "updated", "customer_id": existing.id, "name": existing.name}
                customer = Customer(
                    organization_id=org.id,
                    phone=phone,
                    name=name,
                    email=args.get("email"),
                    notes=args.get("notes")
                )
                db.add(customer)
                db.commit()
                return {"status": "created", "customer_id": customer.id, "name": customer.name}

            # 3. get_business_information
            elif tool_name == "get_business_information":
                settings = db.query(BusinessSettings).filter_by(organization_id=org.id).first()
                hours = db.query(BusinessHours).filter_by(organization_id=org.id).order_by(BusinessHours.day_of_week.asc()).all()
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                hours_desc = []
                for h in hours:
                    d_name = day_names[h.day_of_week]
                    if h.is_closed:
                        hours_desc.append(f"{d_name}: Closed")
                    else:
                        hours_desc.append(f"{d_name}: {h.open_time} - {h.close_time}")

                return {
                    "business_name": org.name,
                    "address": settings.address if settings else None,
                    "phone": org.phone,
                    "operating_hours": hours_desc,
                    "cancellation_policy": settings.cancellation_policy if settings else "4 hours notice required.",
                    "timezone": org.timezone
                }

            # 4. get_services
            elif tool_name == "get_services":
                services = db.query(Service).filter_by(organization_id=org.id, is_active=True).all()
                return {
                    "services": [
                        {
                            "id": s.id,
                            "name": s.name,
                            "description": s.description,
                            "price": s.price,
                            "currency": s.currency,
                            "duration_minutes": s.duration_minutes
                        }
                        for s in services
                    ]
                }

            # 5. search_knowledge_base
            elif tool_name == "search_knowledge_base":
                query = args.get("query", "")
                if not query:
                    return {"status": "error", "message": "Query parameter is required."}
                result = RAGService.answer_query(db, org, query, top_k=3)
                return {
                    "answer": result.answer,
                    "has_verified_info": result.has_answer,
                    "sources": [s.filename for s in result.sources]
                }

            # 6. check_availability
            elif tool_name == "check_availability":
                service_id = args.get("service_id")
                date_str = args.get("date")  # YYYY-MM-DD
                service_name = args.get("service_name")

                # Resolve service by name if ID was not provided
                if not service_id and service_name:
                    s_match = db.query(Service).filter(
                        Service.organization_id == org.id,
                        Service.is_active == True,
                        Service.name.ilike(f"%{service_name}%")
                    ).first()
                    if s_match:
                        service_id = s_match.id

                if not service_id:
                    # Default to first active service
                    first_s = db.query(Service).filter_by(organization_id=org.id, is_active=True).first()
                    if first_s:
                        service_id = first_s.id
                    else:
                        return {"status": "error", "message": "No active services found."}

                if not date_str:
                    target_date = date.today()
                else:
                    try:
                        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        target_date = date.today()

                avail = AvailabilityService.get_available_slots(
                    db=db,
                    org=org,
                    service_id=service_id,
                    target_date=target_date,
                    staff_id=args.get("staff_id")
                )
                if not avail.is_available:
                    return {
                        "date": str(target_date),
                        "service": avail.service_name,
                        "available": False,
                        "message": avail.reason
                    }

                # Return available times formatted for spoken voice
                times = [s.formatted_time for s in avail.available_slots[:8]]
                return {
                    "date": str(target_date),
                    "service_id": avail.service_id,
                    "service_name": avail.service_name,
                    "available": True,
                    "available_slots": times,
                    "raw_slots": [
                        {
                            "start_time": s.start_time.isoformat(),
                            "formatted_time": s.formatted_time,
                            "staff_id": s.available_staff_id,
                            "staff_name": s.available_staff_name
                        }
                        for s in avail.available_slots[:8]
                    ]
                }

            # 7. book_appointment
            elif tool_name == "book_appointment":
                service_id = args.get("service_id")
                service_name = args.get("service_name")
                if not service_id and service_name:
                    s_match = db.query(Service).filter(
                        Service.organization_id == org.id,
                        Service.is_active == True,
                        Service.name.ilike(f"%{service_name}%")
                    ).first()
                    if s_match:
                        service_id = s_match.id

                if not service_id:
                    first_s = db.query(Service).filter_by(organization_id=org.id, is_active=True).first()
                    if first_s:
                        service_id = first_s.id
                    else:
                        return {"status": "error", "message": "Service could not be determined."}

                start_time_raw = args.get("start_time") or args.get("date_time")
                if not start_time_raw:
                    return {"status": "error", "message": "Appointment date and time is required."}

                try:
                    start_dt = datetime.fromisoformat(start_time_raw.replace("Z", "+00:00"))
                except ValueError:
                    return {"status": "error", "message": f"Invalid date time format '{start_time_raw}'."}

                appt_create = AppointmentCreate(
                    service_id=service_id,
                    customer_phone=args.get("customer_phone") or args.get("phone"),
                    customer_name=args.get("customer_name") or args.get("name"),
                    customer_email=args.get("customer_email"),
                    staff_id=args.get("staff_id"),
                    start_time=start_dt,
                    notes=f"Booked via VoiceDesk Voice Receptionist. {args.get('notes', '')}".strip(),
                    call_id=call_id_context
                )

                appt_resp = AppointmentService.book_appointment(db, org, appt_create)
                return {
                    "status": "confirmed",
                    "appointment_id": appt_resp.id,
                    "customer_name": appt_resp.customer_name,
                    "service_name": appt_resp.service_name,
                    "start_time": appt_resp.start_time.isoformat(),
                    "message": f"Appointment successfully confirmed for {appt_resp.customer_name} on {appt_resp.start_time.strftime('%B %d at %I:%M %p')}."
                }

            # 8. reschedule_appointment
            elif tool_name == "reschedule_appointment":
                appointment_id = args.get("appointment_id")
                # Look up by phone if ID not directly available
                if not appointment_id and args.get("phone"):
                    phone = normalize_phone(args.get("phone"))
                    cust = db.query(Customer).filter_by(organization_id=org.id, phone=phone).first()
                    if cust:
                        latest_appt = db.query(Appointment).filter_by(
                            organization_id=org.id,
                            customer_id=cust.id,
                            status="Confirmed"
                        ).order_by(Appointment.start_time.asc()).first()
                        if latest_appt:
                            appointment_id = latest_appt.id

                if not appointment_id:
                    return {"status": "error", "message": "Could not identify which appointment to reschedule."}

                new_start_raw = args.get("new_date_time") or args.get("new_start_time")
                if not new_start_raw:
                    return {"status": "error", "message": "New appointment date and time is required."}

                new_start_dt = datetime.fromisoformat(new_start_raw.replace("Z", "+00:00"))
                resched_req = AppointmentReschedule(
                    new_start_time=new_start_dt,
                    reason=args.get("reason", "Rescheduled via voice call")
                )
                appt_resp = AppointmentService.reschedule_appointment(db, org, appointment_id, resched_req)
                return {
                    "status": "rescheduled",
                    "appointment_id": appt_resp.id,
                    "new_start_time": appt_resp.start_time.isoformat(),
                    "message": f"Appointment rescheduled successfully to {appt_resp.start_time.strftime('%B %d at %I:%M %p')}."
                }

            # 9. cancel_appointment
            elif tool_name == "cancel_appointment":
                appointment_id = args.get("appointment_id")
                if not appointment_id and args.get("phone"):
                    phone = normalize_phone(args.get("phone"))
                    cust = db.query(Customer).filter_by(organization_id=org.id, phone=phone).first()
                    if cust:
                        latest_appt = db.query(Appointment).filter_by(
                            organization_id=org.id,
                            customer_id=cust.id,
                            status="Confirmed"
                        ).order_by(Appointment.start_time.asc()).first()
                        if latest_appt:
                            appointment_id = latest_appt.id

                if not appointment_id:
                    return {"status": "error", "message": "Could not locate appointment to cancel."}

                cancel_req = AppointmentCancel(reason=args.get("reason", "Customer cancelled via voice call"))
                appt_resp = AppointmentService.cancel_appointment(db, org, appointment_id, cancel_req)
                return {
                    "status": "cancelled",
                    "appointment_id": appt_resp.id,
                    "message": "Appointment has been cancelled as requested."
                }

            # 10. transfer_to_human
            elif tool_name == "transfer_to_human":
                settings = db.query(BusinessSettings).filter_by(organization_id=org.id).first()
                transfer_phone = settings.human_transfer_phone if settings else None
                reason = args.get("reason", "Customer requested human assistance")

                if call_id_context:
                    call_rec = db.query(Call).filter_by(id=call_id_context).first()
                    if call_rec:
                        call_rec.escalation_status = "requested"
                        call_rec.transfer_reason = reason
                        call_rec.transfer_phone_number = transfer_phone
                        db.commit()

                if not transfer_phone:
                    return {
                        "status": "unavailable",
                        "message": "A transfer phone number is not currently configured for this business."
                    }

                return {
                    "status": "transfer_initiated",
                    "destination": transfer_phone,
                    "reason": reason,
                    "message": f"Transferring your call to our staff at {transfer_phone}. Please stay on the line."
                }

            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    @classmethod
    def process_webhook(cls, db: Session, payload: Dict[str, Any], org_id_param: Optional[str] = None) -> Dict[str, Any]:
        """
        Idempotent processor for Vapi webhook events:
        - assistant-request
        - tool-calls / function-call
        - status-update
        - end-of-call-report
        """
        message = payload.get("message") or {}
        msg_type = message.get("type", "")
        call_obj = message.get("call") or {}
        vapi_call_id = call_obj.get("id") or message.get("callId")

        # Resolve organization
        org = cls.resolve_organization(db, call_obj, org_id_param)
        if not org:
            return {"error": "Organization could not be determined."}

        # Idempotency check:
        # If an explicit event id is passed, enforce deduplication.
        explicit_event_id = message.get("id")
        if explicit_event_id:
            existing_event = db.query(WebhookEvent).filter_by(event_id=explicit_event_id).first()
            if existing_event and existing_event.status == "processed":
                return {"status": "duplicate_ignored", "event_id": explicit_event_id}
            event_id = explicit_event_id
        else:
            event_id = f"evt_{uuid.uuid4().hex}"

        # Record webhook event
        event_rec = WebhookEvent(
            organization_id=org.id,
            event_id=event_id,
            event_type=msg_type,
            payload_json=json.dumps(payload)[:5000],
            status="received"
        )
        db.add(event_rec)
        db.flush()

        # Handle message types
        response_data: Dict[str, Any] = {}

        # A. assistant-request: Customize assistant greeting & configuration dynamically
        if msg_type == "assistant-request":
            settings = db.query(BusinessSettings).filter_by(organization_id=org.id).first()
            greeting = settings.ai_greeting_en if settings else f"Welcome to {org.name}! How may I help you today?"
            sys_prompt = f"""You are the inbound AI receptionist for {org.name}.
Always speak in a warm, polite, and professional tone.
Identify the caller's need, answer questions accurately using your knowledge base tool,
check availability when appointments are requested, and confirm all booking details.
If the customer asks for a human or the matter is too sensitive, use the transfer_to_human tool.
"""
            response_data = {
                "assistant": {
                    "firstMessage": greeting,
                    "model": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "system", "content": sys_prompt}]
                    }
                }
            }

        # B. tool-calls / function-call
        elif msg_type in ["tool-calls", "function-call"]:
            tool_calls = message.get("toolCalls") or message.get("toolCallList") or []
            results = []

            # Check if call record exists
            db_call = db.query(Call).filter_by(vapi_call_id=vapi_call_id).first() if vapi_call_id else None

            for tc in tool_calls:
                tc_id = tc.get("id") or tc.get("toolCallId")
                func_info = tc.get("function") or {}
                fn_name = func_info.get("name") or tc.get("name")
                fn_args = func_info.get("arguments") or tc.get("arguments") or {}
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except Exception:
                        fn_args = {}

                tool_result = cls.execute_tool(
                    db=db,
                    org=org,
                    tool_name=fn_name,
                    args=fn_args,
                    call_id_context=db_call.id if db_call else None
                )
                results.append({
                    "toolCallId": tc_id,
                    "result": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                })

            response_data = {"results": results}

        # C. end-of-call-report: Capture call intelligence, transcript, and summary
        elif msg_type == "end-of-call-report":
            caller_phone_raw = call_obj.get("customer", {}).get("number") or message.get("customer", {}).get("number") or "+910000000000"
            caller_phone = normalize_phone(caller_phone_raw)
            duration_s = int(message.get("durationSeconds") or call_obj.get("durationSeconds") or 0)
            cost = float(message.get("cost") or call_obj.get("cost") or 0.0)
            rec_url = message.get("recordingUrl") or call_obj.get("recordingUrl")
            transcript_text = message.get("transcript") or ""
            summary_text = message.get("summary") or ""
            analysis = message.get("analysis") or {}

            # Link customer
            customer = db.query(Customer).filter_by(organization_id=org.id, phone=caller_phone).first()

            # Determine outcome
            outcome = "inquiry_resolved"
            if "booked" in transcript_text.lower() or "confirmed" in transcript_text.lower():
                outcome = "booked"
            elif "transfer" in transcript_text.lower():
                outcome = "transferred"
            elif duration_s < 10:
                outcome = "missed"

            # Create or update Call record
            call_rec = db.query(Call).filter_by(vapi_call_id=vapi_call_id).first() if vapi_call_id else None
            if not call_rec:
                call_rec = Call(
                    organization_id=org.id,
                    customer_id=customer.id if customer else None,
                    vapi_call_id=vapi_call_id,
                    caller_phone=caller_phone,
                    direction="inbound",
                    status="completed",
                    duration_seconds=duration_s,
                    cost=cost,
                    recording_url=rec_url,
                    outcome=outcome
                )
                db.add(call_rec)
                db.flush()
            else:
                call_rec.status = "completed"
                call_rec.duration_seconds = duration_s
                call_rec.cost = cost
                call_rec.recording_url = rec_url
                call_rec.outcome = outcome

            # Save CallTranscript
            if transcript_text:
                transcript_rec = db.query(CallTranscript).filter_by(call_id=call_rec.id).first()
                if not transcript_rec:
                    transcript_rec = CallTranscript(
                        call_id=call_rec.id,
                        full_transcript=transcript_text,
                        messages_json=json.dumps(message.get("artifact", {}).get("messages", []))
                    )
                    db.add(transcript_rec)
                else:
                    transcript_rec.full_transcript = transcript_text

            # Save CallSummary
            if summary_text or analysis:
                summary_rec = db.query(CallSummary).filter_by(call_id=call_rec.id).first()
                if not summary_rec:
                    summary_rec = CallSummary(
                        call_id=call_rec.id,
                        summary_text=summary_text or "Call completed.",
                        intent=analysis.get("structuredData", {}).get("intent", "appointment_booking"),
                        sentiment=analysis.get("structuredData", {}).get("sentiment", "positive")
                    )
                    db.add(summary_rec)

            response_data = {"status": "call_recorded", "call_id": call_rec.id}

        event_rec.status = "processed"
        db.commit()
        return response_data
