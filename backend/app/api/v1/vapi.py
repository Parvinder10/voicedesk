from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, Header, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org, verify_vapi_secret
from app.models import Organization, BusinessSettings
from app.services.vapi_service import VapiService
from app.config import settings

router = APIRouter(prefix="/vapi", tags=["Vapi Voice Integration"])


@router.get("/health")
def vapi_health():
    """Check Vapi integration readiness and configuration status."""
    return {
        "status": "ready",
        "has_vapi_api_key": bool(settings.VAPI_API_KEY),
        "webhook_endpoint": f"{settings.API_V1_STR}/vapi/webhook",
        "supported_tools": [
            "identify_customer",
            "search_knowledge_base",
            "get_business_information",
            "get_services",
            "check_availability",
            "book_appointment",
            "reschedule_appointment",
            "cancel_appointment",
            "create_customer",
            "transfer_to_human"
        ]
    }


@router.post("/webhook")
async def handle_vapi_webhook(
    request: Request,
    org_id: Optional[str] = Query(None, description="Optional tenant organization ID"),
    db: Session = Depends(get_db)
):
    """
    Main webhook entry point for real Vapi inbound calling events.
    Dispatches assistant-request, tool-calls, and end-of-call-report with idempotency.
    """
    # Verify signature/secret if header provided
    vapi_secret = request.headers.get("x-vapi-secret")
    if settings.VAPI_WEBHOOK_SECRET and vapi_secret and vapi_secret != settings.VAPI_WEBHOOK_SECRET:
        return {"error": "Unauthorized webhook secret"}

    payload: Dict[str, Any] = await request.json()
    result = VapiService.process_webhook(db=db, payload=payload, org_id_param=org_id)
    return result


@router.post("/assistant/sync")
def sync_assistant_configuration(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Generate the complete production assistant configuration payload for Vapi,
    including function tool schemas, instructions, multilingual greetings, and business context.
    """
    settings_rec = db.query(BusinessSettings).filter_by(organization_id=org.id).first()
    greeting = settings_rec.ai_greeting_en if settings_rec else f"Hello, thank you for calling {org.name}."
    transfer_num = settings_rec.human_transfer_phone if settings_rec else "+919999999999"

    # Tool definitions according to OpenAI / Vapi function calling specs
    tools = [
        {
            "type": "function",
            "function": {
                "name": "identify_customer",
                "description": "Look up existing customer profile, history, and previous appointments by phone number.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string", "description": "Customer phone number in international or national format"}
                    },
                    "required": ["phone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Query official business documents for pricing, policies, services, doctor credentials, and clinic guidelines.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The specific question or information to look up"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_business_information",
                "description": "Get operating hours, clinic address, cancellation policy, and general business information.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_services",
                "description": "Get full list of services, prices, and standard appointment durations.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": "Check real-time appointment slot availability for a specified service and date.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Name of the requested service"},
                        "date": {"type": "string", "description": "Target date in YYYY-MM-DD format"}
                    },
                    "required": ["date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "book_appointment",
                "description": "Book a confirmed appointment slot for the customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service name to book"},
                        "date_time": {"type": "string", "description": "ISO 8601 formatted start datetime"},
                        "customer_phone": {"type": "string", "description": "Customer phone number"},
                        "customer_name": {"type": "string", "description": "Customer full name"},
                        "notes": {"type": "string", "description": "Any special notes or requirements"}
                    },
                    "required": ["date_time", "customer_phone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "reschedule_appointment",
                "description": "Reschedule an existing appointment to a new date and time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string", "description": "Customer phone number"},
                        "new_date_time": {"type": "string", "description": "New ISO 8601 start datetime"},
                        "reason": {"type": "string", "description": "Reason for rescheduling"}
                    },
                    "required": ["phone", "new_date_time"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "cancel_appointment",
                "description": "Cancel an existing appointment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string", "description": "Customer phone number"},
                        "reason": {"type": "string", "description": "Reason for cancellation"}
                    },
                    "required": ["phone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "transfer_to_human",
                "description": "Transfer the caller to human staff when requested or when issue cannot be resolved by AI.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string", "description": "Reason for transfer"}
                    },
                    "required": ["reason"]
                }
            }
        }
    ]

    assistant_config = {
        "name": f"{org.name} Voice Receptionist",
        "firstMessage": greeting,
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en"
        },
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": f"You are the professional voice receptionist for {org.name}. Answer inquiries accurately, book appointments using check_availability and book_appointment, and transfer to {transfer_num} if needed."
                }
            ],
            "tools": tools
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "sarah"
        }
    }

    return {
        "organization_id": org.id,
        "assistant_config": assistant_config,
        "server_webhook_url": f"/api/v1/vapi/webhook?org_id={org.id}"
    }
