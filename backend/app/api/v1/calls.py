from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org
from app.models import Call, CallTranscript, CallSummary, Customer, Organization
from app.schemas.vapi import CallResponse, CallTranscriptResponse

router = APIRouter(prefix="/calls", tags=["Calls"])


@router.get("", response_model=List[CallResponse])
def list_calls(
    status: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """List inbound voice calls with details, outcomes, transcripts, and duration."""
    query = db.query(Call).filter(Call.organization_id == org.id)
    if status:
        query = query.filter(Call.status == status)
    if outcome:
        query = query.filter(Call.outcome == outcome)
    if customer_id:
        query = query.filter(Call.customer_id == customer_id)

    calls = query.order_by(Call.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for c in calls:
        summary_text = c.summary.summary_text if c.summary else None
        intent = c.summary.intent if c.summary else None
        sentiment = c.summary.sentiment if c.summary else None
        customer_name = c.customer.name if c.customer else None

        results.append(
            CallResponse(
                id=c.id,
                organization_id=c.organization_id,
                customer_id=c.customer_id,
                vapi_call_id=c.vapi_call_id,
                caller_phone=c.caller_phone,
                recipient_phone=c.recipient_phone,
                direction=c.direction,
                status=c.status,
                duration_seconds=c.duration_seconds,
                cost=c.cost,
                recording_url=c.recording_url,
                started_at=c.started_at,
                ended_at=c.ended_at,
                escalation_status=c.escalation_status,
                transfer_phone_number=c.transfer_phone_number,
                transfer_reason=c.transfer_reason,
                outcome=c.outcome,
                created_at=c.created_at,
                updated_at=c.updated_at,
                customer_name=customer_name,
                summary_text=summary_text,
                intent=intent,
                sentiment=sentiment
            )
        )
    return results


@router.get("/{id}", response_model=CallResponse)
def get_call(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve details for a specific call."""
    c = db.query(Call).filter(Call.id == id, Call.organization_id == org.id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call record not found.")

    return CallResponse(
        id=c.id,
        organization_id=c.organization_id,
        customer_id=c.customer_id,
        vapi_call_id=c.vapi_call_id,
        caller_phone=c.caller_phone,
        recipient_phone=c.recipient_phone,
        direction=c.direction,
        status=c.status,
        duration_seconds=c.duration_seconds,
        cost=c.cost,
        recording_url=c.recording_url,
        started_at=c.started_at,
        ended_at=c.ended_at,
        escalation_status=c.escalation_status,
        transfer_phone_number=c.transfer_phone_number,
        transfer_reason=c.transfer_reason,
        outcome=c.outcome,
        created_at=c.created_at,
        updated_at=c.updated_at,
        customer_name=c.customer.name if c.customer else None,
        summary_text=c.summary.summary_text if c.summary else None,
        intent=c.summary.intent if c.summary else None,
        sentiment=c.summary.sentiment if c.summary else None
    )


@router.get("/{id}/transcript", response_model=CallTranscriptResponse)
def get_call_transcript(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve full transcript text and conversation message turns."""
    c = db.query(Call).filter(Call.id == id, Call.organization_id == org.id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call record not found.")

    transcript = db.query(CallTranscript).filter_by(call_id=c.id).first()
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not available for this call.")

    import json
    try:
        messages = json.loads(transcript.messages_json)
    except Exception:
        messages = []

    return CallTranscriptResponse(
        call_id=c.id,
        full_transcript=transcript.full_transcript,
        messages=messages,
        created_at=transcript.created_at
    )
