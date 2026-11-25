from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class CallResponse(BaseModel):
    id: str
    organization_id: str
    customer_id: Optional[str] = None
    vapi_call_id: Optional[str] = None
    caller_phone: str
    recipient_phone: Optional[str] = None
    direction: str
    status: str
    duration_seconds: int
    cost: float
    recording_url: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    escalation_status: str
    transfer_phone_number: Optional[str] = None
    transfer_reason: Optional[str] = None
    outcome: str
    created_at: datetime
    updated_at: datetime
    
    customer_name: Optional[str] = None
    summary_text: Optional[str] = None
    intent: Optional[str] = None
    sentiment: Optional[str] = None

    class Config:
        from_attributes = True


class CallTranscriptResponse(BaseModel):
    call_id: str
    full_transcript: str
    messages: List[Dict[str, Any]] = []
    created_at: datetime


class VapiToolCallItem(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, Any]


class VapiWebhookMessage(BaseModel):
    type: str  # "assistant-request", "tool-calls", "status-update", "end-of-call-report", "transfer-update"
    call: Optional[Dict[str, Any]] = None
    toolCalls: Optional[List[VapiToolCallItem]] = None
    toolCallList: Optional[List[Dict[str, Any]]] = None  # legacy alternative
    transcript: Optional[str] = None
    summary: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    artifact: Optional[Dict[str, Any]] = None
    timestamp: Optional[Union[str, int, float]] = None


class VapiWebhookPayload(BaseModel):
    message: VapiWebhookMessage

    class Config:
        extra = "allow"


class VapiToolResult(BaseModel):
    toolCallId: str
    result: str


class VapiToolResponse(BaseModel):
    results: List[VapiToolResult]
