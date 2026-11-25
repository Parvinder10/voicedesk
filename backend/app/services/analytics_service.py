from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Organization, Call, Appointment, Customer, Service


class AnalyticsService:
    @staticmethod
    def get_dashboard_overview(db: Session, org: Organization) -> Dict[str, Any]:
        """Calculates live persisted metrics for the organization dashboard."""
        # Call statistics
        total_calls = db.query(func.count(Call.id)).filter(Call.organization_id == org.id).scalar() or 0
        answered_calls = db.query(func.count(Call.id)).filter(
            Call.organization_id == org.id,
            Call.status == "completed"
        ).scalar() or 0
        missed_calls = db.query(func.count(Call.id)).filter(
            Call.organization_id == org.id,
            Call.outcome == "missed"
        ).scalar() or 0
        human_handoffs = db.query(func.count(Call.id)).filter(
            Call.organization_id == org.id,
            Call.escalation_status.in_(["requested", "completed"])
        ).scalar() or 0

        # Duration metrics
        avg_duration = db.query(func.avg(Call.duration_seconds)).filter(
            Call.organization_id == org.id,
            Call.status == "completed"
        ).scalar() or 0.0

        # Appointment statistics
        total_bookings = db.query(func.count(Appointment.id)).filter(
            Appointment.organization_id == org.id
        ).scalar() or 0
        confirmed_bookings = db.query(func.count(Appointment.id)).filter(
            Appointment.organization_id == org.id,
            Appointment.status == "Confirmed"
        ).scalar() or 0
        rescheduled_count = db.query(func.count(Appointment.id)).filter(
            Appointment.organization_id == org.id,
            Appointment.status == "Rescheduled"
        ).scalar() or 0
        cancelled_count = db.query(func.count(Appointment.id)).filter(
            Appointment.organization_id == org.id,
            Appointment.status == "Cancelled"
        ).scalar() or 0
        completed_count = db.query(func.count(Appointment.id)).filter(
            Appointment.organization_id == org.id,
            Appointment.status == "Completed"
        ).scalar() or 0

        # Customer count
        total_customers = db.query(func.count(Customer.id)).filter(
            Customer.organization_id == org.id
        ).scalar() or 0

        # Call outcomes breakdown
        outcomes_query = db.query(
            Call.outcome, func.count(Call.id)
        ).filter(
            Call.organization_id == org.id
        ).group_by(Call.outcome).all()
        outcomes_breakdown = {outcome: count for outcome, count in outcomes_query}

        # Resolution rate
        resolved_count = outcomes_breakdown.get("booked", 0) + outcomes_breakdown.get("inquiry_resolved", 0)
        resolution_rate = round((resolved_count / total_calls * 100), 1) if total_calls > 0 else 100.0

        # Peak calling hours (0 to 23 hour buckets)
        hour_counts = [0] * 24
        all_calls = db.query(Call.created_at).filter(Call.organization_id == org.id).all()
        for c in all_calls:
            if c.created_at:
                hour_counts[c.created_at.hour] += 1

        peak_hours_data = [
            {"hour": f"{h:02d}:00", "calls": hour_counts[h]}
            for h in range(8, 21)  # Focus on business hours 8 AM to 8 PM
        ]

        return {
            "metrics": {
                "total_calls": total_calls,
                "answered_calls": answered_calls,
                "missed_calls": missed_calls,
                "human_handoffs": human_handoffs,
                "average_call_duration_seconds": round(float(avg_duration), 1),
                "resolution_rate_percentage": resolution_rate,
                "total_customers": total_customers,
                "total_appointments": total_bookings,
                "confirmed_appointments": confirmed_bookings,
                "rescheduled_appointments": rescheduled_count,
                "cancelled_appointments": cancelled_count,
                "completed_appointments": completed_count
            },
            "outcomes_breakdown": outcomes_breakdown,
            "peak_calling_hours": peak_hours_data
        }

    @staticmethod
    def get_recent_activity(db: Session, org: Organization, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves unified recent live activity stream of calls and appointments."""
        recent_calls = db.query(Call).filter(
            Call.organization_id == org.id
        ).order_by(Call.created_at.desc()).limit(limit).all()

        recent_appts = db.query(Appointment).filter(
            Appointment.organization_id == org.id
        ).order_by(Appointment.created_at.desc()).limit(limit).all()

        activity_stream = []
        for c in recent_calls:
            activity_stream.append({
                "type": "call",
                "id": c.id,
                "title": f"Inbound Call from {c.caller_phone}",
                "subtitle": f"Outcome: {c.outcome} ({c.duration_seconds}s)",
                "status": c.status,
                "timestamp": c.created_at.isoformat() if c.created_at else None
            })

        for a in recent_appts:
            c_name = a.customer.name if a.customer else "Customer"
            s_name = a.service.name if a.service else "Service"
            activity_stream.append({
                "type": "appointment",
                "id": a.id,
                "title": f"Appointment: {c_name} — {s_name}",
                "subtitle": f"Status: {a.status} at {a.start_time.strftime('%b %d, %I:%M %p') if a.start_time else ''}",
                "status": a.status,
                "timestamp": a.created_at.isoformat() if a.created_at else None
            })

        # Sort by timestamp descending
        activity_stream.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        return activity_stream[:limit]
