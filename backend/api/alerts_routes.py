"""
API routes for alert management
"""

from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional, List
from backend.services.alerts import (
    AlertManager, AlertFactory, NotificationService,
    AlertType, AlertSeverity
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# In-memory alert manager (use DI in production)
alert_manager = AlertManager()
notification_service = NotificationService()


@router.get("/")
def get_alerts(
    team_id: int,
    unread_only: bool = False,
    alert_type: Optional[str] = None,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Get alerts for team
    
    Query params:
        - unread_only: Only unread alerts
        - alert_type: Filter by type (injury, suspension, trade_opportunity, etc.)
    """
    try:
        filter_type = None
        if alert_type:
            filter_type = AlertType[alert_type.upper()]
        
        alerts = alert_manager.get_alerts(
            team_id=str(team_id),
            unread_only=unread_only,
            alert_type=filter_type,
        )
        
        return {
            "team_id": team_id,
            "count": len(alerts),
            "unread_count": len([a for a in alerts if not a.read]),
            "alerts": [a.to_dict() for a in alerts],
        }
    except Exception as e:
        logger.error(f"Alert fetch error: {e}")
        raise HTTPException(500, f"Failed to fetch alerts: {str(e)}")


@router.post("/mark-read/{alert_id}")
def mark_alert_read(
    team_id: int,
    alert_id: str,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Mark alert as read
    """
    success = alert_manager.mark_as_read(str(team_id), alert_id)
    if not success:
        raise HTTPException(404, "Alert not found")
    
    return {"success": True, "alert_id": alert_id}


@router.delete("/{alert_id}")
def dismiss_alert(
    team_id: int,
    alert_id: str,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Dismiss/delete alert
    """
    success = alert_manager.dismiss_alert(str(team_id), alert_id)
    if not success:
        raise HTTPException(404, "Alert not found")
    
    return {"success": True, "alert_id": alert_id}


@router.post("/subscribe")
def subscribe_alerts(
    team_id: int,
    alert_types: List[str],
    dml_session: Optional[str] = Cookie(None),
):
    """
    Subscribe team to alert types
    
    Alert types:
    - injury
    - suspension
    - lineup_lock
    - trade_opportunity
    - player_out
    - fixture_reminder
    - prediction_update
    """
    try:
        types_enum = [AlertType[t.upper()] for t in alert_types]
        alert_manager.subscribe(str(team_id), types_enum)
        
        return {
            "success": True,
            "team_id": team_id,
            "subscribed_to": alert_types,
        }
    except Exception as e:
        logger.error(f"Subscription error: {e}")
        raise HTTPException(400, f"Invalid alert types: {str(e)}")


@router.post("/injury")
async def create_injury_alert(
    team_id: int,
    player_id: int,
    player_name: str,
    severity: str,  # minor, major, out_for_season
    dml_session: Optional[str] = Cookie(None),
):
    """
    Create injury alert for team
    
    Severity: minor, major, out_for_season
    """
    try:
        alert = AlertFactory.injury_alert(
            team_id=str(team_id),
            player_id=str(player_id),
            player_name=player_name,
            severity=severity,
        )
        
        # Send notification
        await notification_service.notify_injury(
            team_id=str(team_id),
            player_id=str(player_id),
            player_name=player_name,
            severity=severity,
        )
        
        return alert.to_dict()
    except Exception as e:
        logger.error(f"Injury alert creation error: {e}")
        raise HTTPException(500, f"Failed to create alert: {str(e)}")


@router.post("/suspension")
async def create_suspension_alert(
    team_id: int,
    player_id: int,
    player_name: str,
    rounds_out: int,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Create suspension alert for team
    """
    try:
        alert = AlertFactory.suspension_alert(
            team_id=str(team_id),
            player_id=str(player_id),
            player_name=player_name,
            rounds_out=rounds_out,
        )
        
        # Send notification
        await notification_service.notify_suspension(
            team_id=str(team_id),
            player_id=str(player_id),
            player_name=player_name,
            rounds_out=rounds_out,
        )
        
        return alert.to_dict()
    except Exception as e:
        logger.error(f"Suspension alert creation error: {e}")
        raise HTTPException(500, f"Failed to create alert: {str(e)}")


@router.get("/health")
def alerts_health():
    """
    Alert system health check
    """
    total_alerts = sum(len(alerts) for alerts in alert_manager.alerts.values())
    
    return {
        "status": "healthy",
        "total_alerts": total_alerts,
        "teams_with_alerts": len(alert_manager.alerts),
        "subscribed_teams": len(alert_manager.subscriptions),
    }
