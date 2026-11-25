import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="organization", cascade="all, delete-orphan")
    staff_members = relationship("Staff", back_populates="organization", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="organization", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="organization", cascade="all, delete-orphan")
    business_hours = relationship("BusinessHours", back_populates="organization", cascade="all, delete-orphan")
    holidays = relationship("Holiday", back_populates="organization", cascade="all, delete-orphan")
    availability_rules = relationship("AvailabilityRule", back_populates="organization", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")
    settings = relationship("BusinessSettings", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="owner", nullable=False)  # owner, admin, staff
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    phone = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "phone", name="uq_org_customer_phone"),
        Index("ix_org_customer_phone", "organization_id", "phone"),
    )

    organization = relationship("Organization", back_populates="customers")
    appointments = relationship("Appointment", back_populates="customer", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="customer")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    title = Column(String(100), nullable=True)  # e.g., Senior Stylist, General Physician
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="staff_members")
    appointments = relationship("Appointment", back_populates="staff")
    availability_rules = relationship("AvailabilityRule", back_populates="staff", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=30, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_org_service_name", "organization_id", "name"),
    )

    organization = relationship("Organization", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(String(36), ForeignKey("staff.id", ondelete="SET NULL"), nullable=True, index=True)
    call_id = Column(String(36), ForeignKey("calls.id", ondelete="SET NULL"), nullable=True, index=True)
    
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Statuses: Pending, Confirmed, Rescheduled, Cancelled, Completed, No-show
    status = Column(String(50), default="Confirmed", nullable=False, index=True)
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_app_org_timeslot", "organization_id", "start_time", "end_time"),
        Index("ix_app_staff_timeslot", "staff_id", "start_time", "end_time"),
    )

    organization = relationship("Organization", back_populates="appointments")
    customer = relationship("Customer", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    staff = relationship("Staff", back_populates="appointments")
    call = relationship("Call", back_populates="appointments")


class BusinessHours(Base):
    __tablename__ = "business_hours"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    open_time = Column(String(10), nullable=False)  # "09:00"
    close_time = Column(String(10), nullable=False)  # "18:00"
    is_closed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "day_of_week", name="uq_org_day_of_week"),
    )

    organization = relationship("Organization", back_populates="business_hours")


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, index=True)
    is_recurring = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "date", name="uq_org_holiday_date"),
    )

    organization = relationship("Organization", back_populates="holidays")


class AvailabilityRule(Base):
    __tablename__ = "availability_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(String(36), ForeignKey("staff.id", ondelete="CASCADE"), nullable=True, index=True)
    rule_type = Column(String(50), nullable=False)  # break, vacation, buffer, custom_hours
    start_datetime = Column(DateTime(timezone=True), nullable=True)
    end_datetime = Column(DateTime(timezone=True), nullable=True)
    day_of_week = Column(Integer, nullable=True)
    start_time = Column(String(10), nullable=True)  # "13:00"
    end_time = Column(String(10), nullable=True)    # "14:00"
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="availability_rules")
    staff = relationship("Staff", back_populates="availability_rules")


class Call(Base):
    __tablename__ = "calls"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    vapi_call_id = Column(String(100), unique=True, index=True, nullable=True)
    caller_phone = Column(String(50), nullable=False, index=True)
    recipient_phone = Column(String(50), nullable=True)
    direction = Column(String(20), default="inbound", nullable=False)
    status = Column(String(50), default="completed", nullable=False, index=True)  # queued, ringing, in-progress, completed, transferred, failed
    duration_seconds = Column(Integer, default=0, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)
    recording_url = Column(String(500), nullable=True)
    stereo_recording_url = Column(String(500), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    escalation_status = Column(String(50), default="none", nullable=False)  # none, requested, completed, failed
    transfer_phone_number = Column(String(50), nullable=True)
    transfer_reason = Column(String(255), nullable=True)
    outcome = Column(String(50), default="resolved", nullable=False, index=True)  # booked, inquiry_resolved, transferred, cancelled, missed, failed
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="calls")
    customer = relationship("Customer", back_populates="calls")
    transcript = relationship("CallTranscript", back_populates="call", uselist=False, cascade="all, delete-orphan")
    summary = relationship("CallSummary", back_populates="call", uselist=False, cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="call")


class CallTranscript(Base):
    __tablename__ = "call_transcripts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    call_id = Column(String(36), ForeignKey("calls.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    full_transcript = Column(Text, nullable=False)
    messages_json = Column(Text, default="[]", nullable=False)  # Stored conversation turns
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    call = relationship("Call", back_populates="transcript")


class CallSummary(Base):
    __tablename__ = "call_summaries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    call_id = Column(String(36), ForeignKey("calls.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True, index=True)
    sentiment = Column(String(50), nullable=True)  # positive, neutral, negative, urgent
    action_items = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    call = relationship("Call", back_populates="summary")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, txt, faq, pricing
    file_size_bytes = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, indexed, failed
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    embedding_json = Column(Text, nullable=True)  # JSON serialized vector representation
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_doc_chunk_org", "organization_id", "document_id"),
    )

    document = relationship("Document", back_populates="chunks")


class BusinessSettings(Base):
    __tablename__ = "business_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    business_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    industry = Column(String(100), default="clinic", nullable=False)  # clinic, salon, education, real_estate, home_service
    address = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    human_transfer_phone = Column(String(50), nullable=True)
    default_appointment_duration = Column(Integer, default=30, nullable=False)
    buffer_time_minutes = Column(Integer, default=10, nullable=False)
    max_booking_days_in_advance = Column(Integer, default=30, nullable=False)
    min_booking_notice_hours = Column(Integer, default=2, nullable=False)
    cancellation_notice_hours = Column(Integer, default=4, nullable=False)
    cancellation_policy = Column(Text, nullable=True)
    ai_greeting_en = Column(Text, nullable=True)
    ai_greeting_hi = Column(Text, nullable=True)
    supported_languages = Column(String(50), default="en,hi", nullable=False)
    prompt_instructions = Column(Text, nullable=True)
    vapi_assistant_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="settings")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    event_id = Column(String(255), unique=True, index=True, nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    payload_json = Column(Text, nullable=False)
    status = Column(String(50), default="received", nullable=False)  # received, processed, duplicate, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., create, update, delete, book, cancel
    entity_type = Column(String(100), nullable=False)  # appointment, customer, service, document
    entity_id = Column(String(100), nullable=True)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
