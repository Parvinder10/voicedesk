from datetime import datetime, timedelta, timezone
from typing import Optional, List
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status
from app.models import (
    Organization, Appointment, Service, Customer, Staff,
    BusinessSettings, AuditLog
)
from app.schemas.appointment import (
    AppointmentCreate, AppointmentReschedule, AppointmentCancel, AppointmentResponse
)
from app.api.v1.customers import normalize_phone


class AppointmentService:
    @staticmethod
    def _format_appointment_response(appt: Appointment) -> AppointmentResponse:
        return AppointmentResponse(
            id=appt.id,
            organization_id=appt.organization_id,
            customer_id=appt.customer_id,
            service_id=appt.service_id,
            staff_id=appt.staff_id,
            call_id=appt.call_id,
            start_time=appt.start_time,
            end_time=appt.end_time,
            status=appt.status,
            notes=appt.notes,
            cancellation_reason=appt.cancellation_reason,
            created_at=appt.created_at,
            updated_at=appt.updated_at,
            customer_name=appt.customer.name if appt.customer else None,
            customer_phone=appt.customer.phone if appt.customer else None,
            service_name=appt.service.name if appt.service else None,
            service_price=appt.service.price if appt.service else None,
            staff_name=appt.staff.name if appt.staff else None
        )

    @staticmethod
    def book_appointment(
        db: Session,
        org: Organization,
        data: AppointmentCreate
    ) -> AppointmentResponse:
        # 1. Fetch Service
        service = db.query(Service).filter(
            Service.id == data.service_id,
            Service.organization_id == org.id,
            Service.is_active == True
        ).first()
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found or inactive.")

        # 2. Resolve Customer
        customer = None
        if data.customer_id:
            customer = db.query(Customer).filter(
                Customer.id == data.customer_id,
                Customer.organization_id == org.id
            ).first()
            if not customer:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
        elif data.customer_phone:
            phone = normalize_phone(data.customer_phone)
            customer = db.query(Customer).filter(
                Customer.organization_id == org.id,
                Customer.phone == phone
            ).first()
            if not customer:
                customer = Customer(
                    organization_id=org.id,
                    phone=phone,
                    name=data.customer_name or "Guest Customer",
                    email=data.customer_email
                )
                db.add(customer)
                db.flush()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either customer_id or customer_phone is required."
            )

        # 3. Calculate start and end in UTC
        start_utc = data.start_time
        if start_utc.tzinfo is None:
            # Assume UTC if not provided
            start_utc = start_utc.replace(tzinfo=timezone.utc)
        else:
            start_utc = start_utc.astimezone(timezone.utc)

        end_utc = start_utc + timedelta(minutes=service.duration_minutes)

        # 4. Resolve Staff Member
        staff = None
        if data.staff_id:
            staff = db.query(Staff).filter(
                Staff.id == data.staff_id,
                Staff.organization_id == org.id,
                Staff.is_active == True
            ).first()
            if not staff:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found or inactive.")
        else:
            # Auto-assign first available staff
            all_staff = db.query(Staff).filter(
                Staff.organization_id == org.id,
                Staff.is_active == True
            ).all()
            for s in all_staff:
                conflict = db.query(Appointment).filter(
                    Appointment.organization_id == org.id,
                    Appointment.staff_id == s.id,
                    Appointment.status.in_(["Confirmed", "Pending", "Rescheduled"]),
                    Appointment.start_time < end_utc,
                    Appointment.end_time > start_utc
                ).first()
                if not conflict:
                    staff = s
                    break

            if not staff and all_staff:
                staff = all_staff[0]

        # 5. Concurrency-Safe Overlapping Conflict Check (Transaction boundary)
        with db.begin_nested():
            if staff:
                conflict = db.query(Appointment).filter(
                    Appointment.organization_id == org.id,
                    Appointment.staff_id == staff.id,
                    Appointment.status.in_(["Confirmed", "Pending", "Rescheduled"]),
                    Appointment.start_time < end_utc,
                    Appointment.end_time > start_utc
                ).with_for_update().first() if db.bind.dialect.name == "postgresql" else db.query(Appointment).filter(
                    Appointment.organization_id == org.id,
                    Appointment.staff_id == staff.id,
                    Appointment.status.in_(["Confirmed", "Pending", "Rescheduled"]),
                    Appointment.start_time < end_utc,
                    Appointment.end_time > start_utc
                ).first()

                if conflict:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Double-booking prevented: The selected time slot is already booked for this staff member."
                    )

            # 6. Create Appointment
            appointment = Appointment(
                organization_id=org.id,
                customer_id=customer.id,
                service_id=service.id,
                staff_id=staff.id if staff else None,
                call_id=data.call_id,
                start_time=start_utc,
                end_time=end_utc,
                status="Confirmed",
                notes=data.notes
            )
            db.add(appointment)
            db.flush()

            # Audit log
            audit = AuditLog(
                organization_id=org.id,
                action="appointment_booked",
                entity_type="appointment",
                entity_id=appointment.id,
                details_json=f'{{"customer": "{customer.name}", "service": "{service.name}", "start": "{start_utc.isoformat()}"}}'
            )
            db.add(audit)

        db.commit()
        db.refresh(appointment)
        return AppointmentService._format_appointment_response(appointment)

    @staticmethod
    def reschedule_appointment(
        db: Session,
        org: Organization,
        appointment_id: str,
        data: AppointmentReschedule
    ) -> AppointmentResponse:
        appt = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.organization_id == org.id
        ).first()
        if not appt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

        if appt.status in ["Cancelled", "Completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reschedule an appointment with status: {appt.status}."
            )

        # Compute new time
        new_start_utc = data.new_start_time
        if new_start_utc.tzinfo is None:
            new_start_utc = new_start_utc.replace(tzinfo=timezone.utc)
        else:
            new_start_utc = new_start_utc.astimezone(timezone.utc)

        duration = appt.end_time - appt.start_time
        new_end_utc = new_start_utc + duration
        staff_id = data.staff_id or appt.staff_id

        # Conflict check
        if staff_id:
            conflict = db.query(Appointment).filter(
                Appointment.organization_id == org.id,
                Appointment.staff_id == staff_id,
                Appointment.id != appt.id,
                Appointment.status.in_(["Confirmed", "Pending", "Rescheduled"]),
                Appointment.start_time < new_end_utc,
                Appointment.end_time > new_start_utc
            ).first()
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot reschedule: The new slot conflicts with an existing booking."
                )

        appt.start_time = new_start_utc
        appt.end_time = new_end_utc
        appt.staff_id = staff_id
        appt.status = "Rescheduled"
        if data.reason:
            appt.notes = f"{appt.notes or ''}\nRescheduled: {data.reason}".strip()

        audit = AuditLog(
            organization_id=org.id,
            action="appointment_rescheduled",
            entity_type="appointment",
            entity_id=appt.id,
            details_json=f'{{"new_start": "{new_start_utc.isoformat()}", "reason": "{data.reason}"}}'
        )
        db.add(audit)
        db.commit()
        db.refresh(appt)
        return AppointmentService._format_appointment_response(appt)

    @staticmethod
    def cancel_appointment(
        db: Session,
        org: Organization,
        appointment_id: str,
        data: AppointmentCancel
    ) -> AppointmentResponse:
        appt = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.organization_id == org.id
        ).first()
        if not appt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

        if appt.status == "Cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment is already cancelled.")

        appt.status = "Cancelled"
        appt.cancellation_reason = data.reason

        audit = AuditLog(
            organization_id=org.id,
            action="appointment_cancelled",
            entity_type="appointment",
            entity_id=appt.id,
            details_json=f'{{"reason": "{data.reason}"}}'
        )
        db.add(audit)
        db.commit()
        db.refresh(appt)
        return AppointmentService._format_appointment_response(appt)
