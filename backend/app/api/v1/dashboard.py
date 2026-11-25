from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org
from app.models import Organization
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("/overview")
def get_dashboard_overview(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieve summarized KPIs, resolution rates, outcomes breakdown, and peak calling hours."""
    return AnalyticsService.get_dashboard_overview(db, org)


@router.get("/activity")
def get_dashboard_activity(
    limit: int = Query(10, ge=1, le=50),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Retrieve recent unified event activity stream (calls, bookings, cancellations)."""
    return AnalyticsService.get_recent_activity(db, org, limit=limit)
