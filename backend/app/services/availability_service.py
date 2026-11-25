from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional
import pytz
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import (
    Organization, Service, Staff, BusinessHours, Holiday,
    Appointment, AvailabilityRule, BusinessSettings
)
from app.schemas.availability import AvailabilityResponse, TimeSlot


class AvailabilityService:
    @staticmethod
    def get_available_slots(
        db: Session,
        org: Organization,
        service_id: str,
        target_date: date,
        staff_id: Optional[str] = None
    ) -> AvailabilityResponse:
        # 1. Fetch Service
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.organization_id == org.id,
            Service.is_active == True
        ).first()
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found or inactive.")

        # 2. Setup Timezone
        tz_str = org.timezone or "Asia/Kolkata"
        try:
            local_tz = pytz.timezone(tz_str)
        except Exception:
            local_tz = pytz.timezone("Asia/Kolkata")
            tz_str = "Asia/Kolkata"

        # Current time in org timezone
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone(local_tz)

        # 3. Fetch Settings for booking rules
        settings = db.query(BusinessSettings).filter_by(organization_id=org.id).first()
        buffer_min = settings.buffer_time_minutes if settings else 10
        min_notice_hrs = settings.min_booking_notice_hours if settings else 2
        max_advance_days = settings.max_booking_days_in_advance if settings else 30

        # Check date range
        min_allowed_date = now_local.date()
        max_allowed_date = min_allowed_date + timedelta(days=max_advance_days)
        if target_date < min_allowed_date:
            return AvailabilityResponse(
                date=target_date,
                service_id=service.id,
                service_name=service.name,
                duration_minutes=service.duration_minutes,
                timezone=tz_str,
                is_available=False,
                reason="Cannot book appointments in the past.",
                available_slots=[]
            )
        if target_date > max_allowed_date:
            return AvailabilityResponse(
                date=target_date,
                service_id=service.id,
                service_name=service.name,
                duration_minutes=service.duration_minutes,
                timezone=tz_str,
                is_available=False,
                reason=f"Booking is only allowed up to {max_advance_days} days in advance.",
                available_slots=[]
            )

        # 4. Check Holidays
        holiday = db.query(Holiday).filter(
            Holiday.organization_id == org.id,
            Holiday.date == target_date
        ).first()
        if holiday:
            return AvailabilityResponse(
                date=target_date,
                service_id=service.id,
                service_name=service.name,
                duration_minutes=service.duration_minutes,
                timezone=tz_str,
                is_available=False,
                reason=f"Closed for holiday: {holiday.name}",
                available_slots=[]
            )

        # 5. Check Operating Hours for day of week
        day_of_week = target_date.weekday()  # Monday is 0 and Sunday is 6
        hours = db.query(BusinessHours).filter(
            BusinessHours.organization_id == org.id,
            BusinessHours.day_of_week == day_of_week
        ).first()

        if not hours or hours.is_closed:
            return AvailabilityResponse(
                date=target_date,
                service_id=service.id,
                service_name=service.name,
                duration_minutes=service.duration_minutes,
                timezone=tz_str,
                is_available=False,
                reason="The business is closed on this day.",
                available_slots=[]
            )

        # Parse open and close times
        open_h, open_m = map(int, hours.open_time.split(":"))
        close_h, close_m = map(int, hours.close_time.split(":"))

        day_open_local = local_tz.localize(datetime.combine(target_date, time(open_h, open_m)))
        day_close_local = local_tz.localize(datetime.combine(target_date, time(close_h, close_m)))

        # 6. Fetch Eligible Staff
        if staff_id:
            staff_members = db.query(Staff).filter(
                Staff.id == staff_id,
                Staff.organization_id == org.id,
                Staff.is_active == True
            ).all()
            if not staff_members:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified staff member not found or inactive.")
        else:
            staff_members = db.query(Staff).filter(
                Staff.organization_id == org.id,
                Staff.is_active == True
            ).all()

        if not staff_members:
            return AvailabilityResponse(
                date=target_date,
                service_id=service.id,
                service_name=service.name,
                duration_minutes=service.duration_minutes,
                timezone=tz_str,
                is_available=False,
                reason="No active staff members available for this service.",
                available_slots=[]
            )

        # 7. Fetch existing appointments on target date (range: day_open to day_close)
        day_open_utc = day_open_local.astimezone(timezone.utc)
        day_close_utc = day_close_local.astimezone(timezone.utc)

        existing_appointments = db.query(Appointment).filter(
            Appointment.organization_id == org.id,
            Appointment.status.in_(["Confirmed", "Pending", "Rescheduled"]),
            Appointment.start_time < day_close_utc,
            Appointment.end_time > day_open_utc
        ).all()

        # 8. Fetch availability rules (breaks/vacations)
        rules = db.query(AvailabilityRule).filter(
            AvailabilityRule.organization_id == org.id
        ).all()

        # 9. Iterate candidate slots
        duration = timedelta(minutes=service.duration_minutes)
        step = timedelta(minutes=30)  # slot starting grid step
        min_booking_time_local = now_local + timedelta(hours=min_notice_hrs)

        available_slots: List[TimeSlot] = []
        curr_local = day_open_local

        while curr_local + duration <= day_close_local:
            slot_start_local = curr_local
            slot_end_local = curr_local + duration
            curr_local += step

            # Check min booking notice
            if slot_start_local < min_booking_time_local:
                continue

            slot_start_utc = slot_start_local.astimezone(timezone.utc)
            slot_end_utc = slot_end_local.astimezone(timezone.utc)

            # Find at least one staff member who is free
            assigned_staff: Optional[Staff] = None

            for staff in staff_members:
                # Check overlapping appointment for this staff
                has_appt_conflict = any(
                    appt.staff_id == staff.id and
                    (appt.start_time < slot_end_utc + timedelta(minutes=buffer_min)) and
                    (appt.end_time + timedelta(minutes=buffer_min) > slot_start_utc)
                    for appt in existing_appointments
                )
                if has_appt_conflict:
                    continue

                # Check staff rules (e.g. daily break or vacation)
                has_rule_conflict = False
                for r in rules:
                    if r.staff_id and r.staff_id != staff.id:
                        continue
                    if r.rule_type == "break" and r.start_time and r.end_time:
                        b_sh, b_sm = map(int, r.start_time.split(":"))
                        b_eh, b_em = map(int, r.end_time.split(":"))
                        break_start = local_tz.localize(datetime.combine(target_date, time(b_sh, b_sm)))
                        break_end = local_tz.localize(datetime.combine(target_date, time(b_eh, b_em)))
                        if slot_start_local < break_end and slot_end_local > break_start:
                            has_rule_conflict = True
                            break
                    elif r.rule_type == "vacation" and r.start_datetime and r.end_datetime:
                        if slot_start_utc < r.end_datetime and slot_end_utc > r.start_datetime:
                            has_rule_conflict = True
                            break

                if not has_rule_conflict:
                    assigned_staff = staff
                    break  # Found available staff!

            if assigned_staff:
                formatted_str = slot_start_local.strftime("%I:%M %p")
                available_slots.append(
                    TimeSlot(
                        start_time=slot_start_utc,
                        end_time=slot_end_utc,
                        formatted_time=formatted_str,
                        available_staff_id=assigned_staff.id,
                        available_staff_name=assigned_staff.name
                    )
                )

        return AvailabilityResponse(
            date=target_date,
            service_id=service.id,
            service_name=service.name,
            duration_minutes=service.duration_minutes,
            timezone=tz_str,
            is_available=len(available_slots) > 0,
            reason=None if len(available_slots) > 0 else "All slots on this date are fully booked or outside notice hours.",
            available_slots=available_slots
        )
