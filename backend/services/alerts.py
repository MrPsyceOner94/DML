"""
Alert System for Injury/Suspension Notifications

Handles:
- Injury alerts
- Suspension alerts
- Lineup lock reminders
- Trade opportunity notifications
- Live match updates
"""

from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    INJURY = "injury"
    SUSPENSION = "suspension"
    LINEUP_LOCK = "lineup_lock"
    TRADE_OPPORTUNITY = "trade_opportunity"
    PLAYER_OUT = "player_out"
    FIXTURE_REMINDER = "fixture_reminder"
    PREDICTION_UPDATE = "prediction_update"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"  # Key player out
    HIGH = "high"  # Important update
    MEDIUM = "medium"  # Should review
    LOW = "low"  # FYI


@dataclass
class Alert:
    id: str
    team_id: str
    player_id: Optional[str]
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    created_at: datetime
    expires_at: Optional[datetime]
    read: bool = False
    acted_upon: bool = False
    metadata: Dict = None  # Additional data
    
    def to_dict(self):
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        return data


class AlertManager:
    """Manage alerts for teams/coaches"""
    
    def __init__(self):
        self.alerts: Dict[str, List[Alert]] = {}  # team_id -> alerts
        self.subscriptions: Dict[str, List[AlertType]] = {}  # team_id -> alert types
    
    def create_alert(
        self,
        team_id: str,
        alert_type: AlertType,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        player_id: Optional[str] = None,
        expires_in_hours: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> Alert:
        """Create a new alert"""
        import uuid
        from datetime import timedelta
        
        alert_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = None
        if expires_in_hours:
            expires_at = now + timedelta(hours=expires_in_hours)
        
        alert = Alert(
            id=alert_id,
            team_id=team_id,
            player_id=player_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            created_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        
        if team_id not in self.alerts:
            self.alerts[team_id] = []
        
        self.alerts[team_id].append(alert)
        logger.info(f"Alert created: {alert_id} for team {team_id}")
        
        return alert
    
    def get_alerts(
        self,
        team_id: str,
        unread_only: bool = False,
        alert_type: Optional[AlertType] = None,
    ) -> List[Alert]:
        """Get alerts for a team"""
        alerts = self.alerts.get(team_id, [])
        
        # Filter expired
        now = datetime.utcnow()
        active_alerts = [
            a for a in alerts
            if a.expires_at is None or a.expires_at > now
        ]
        
        # Filter unread
        if unread_only:
            active_alerts = [a for a in active_alerts if not a.read]
        
        # Filter by type
        if alert_type:
            active_alerts = [a for a in active_alerts if a.alert_type == alert_type]
        
        # Sort by severity and recency
        severity_order = {AlertSeverity.CRITICAL: 0, AlertSeverity.HIGH: 1, 
                         AlertSeverity.MEDIUM: 2, AlertSeverity.LOW: 3}
        active_alerts.sort(
            key=lambda a: (severity_order.get(a.severity, 99), -a.created_at.timestamp())
        )
        
        return active_alerts
    
    def mark_as_read(self, team_id: str, alert_id: str) -> bool:
        """Mark alert as read"""
        alerts = self.alerts.get(team_id, [])
        for alert in alerts:
            if alert.id == alert_id:
                alert.read = True
                return True
        return False
    
    def dismiss_alert(self, team_id: str, alert_id: str) -> bool:
        """Dismiss/remove alert"""
        if team_id in self.alerts:
            self.alerts[team_id] = [a for a in self.alerts[team_id] if a.id != alert_id]
            return True
        return False
    
    def subscribe(self, team_id: str, alert_types: List[AlertType]) -> None:
        """Subscribe team to alert types"""
        self.subscriptions[team_id] = alert_types
        logger.info(f"Team {team_id} subscribed to {len(alert_types)} alert types")
    
    def is_subscribed(self, team_id: str, alert_type: AlertType) -> bool:
        """Check if team is subscribed to alert type"""
        subscribed = self.subscriptions.get(team_id, [])
        return alert_type in subscribed


class AlertFactory:
    """Factory for creating specific alert types"""
    
    @staticmethod
    def injury_alert(
        team_id: str,
        player_id: str,
        player_name: str,
        severity: str,
    ) -> Alert:
        """Create injury alert"""
        manager = AlertManager()
        
        severity_map = {
            "out_for_season": AlertSeverity.CRITICAL,
            "major": AlertSeverity.HIGH,
            "minor": AlertSeverity.MEDIUM,
        }
        
        return manager.create_alert(
            team_id=team_id,
            alert_type=AlertType.INJURY,
            title=f"🏥 {player_name} Injured",
            message=f"{player_name} has suffered a {severity} injury and may miss upcoming matches.",
            severity=severity_map.get(severity, AlertSeverity.HIGH),
            player_id=player_id,
            expires_in_hours=72,
            metadata={"injury_severity": severity},
        )
    
    @staticmethod
    def suspension_alert(
        team_id: str,
        player_id: str,
        player_name: str,
        rounds_out: int,
    ) -> Alert:
        """Create suspension alert"""
        manager = AlertManager()
        
        return manager.create_alert(
            team_id=team_id,
            alert_type=AlertType.SUSPENSION,
            title=f"🚫 {player_name} Suspended",
            message=f"{player_name} has been suspended for {rounds_out} round(s).",
            severity=AlertSeverity.CRITICAL if rounds_out > 1 else AlertSeverity.HIGH,
            player_id=player_id,
            expires_in_hours=48,
            metadata={"rounds_suspended": rounds_out},
        )
    
    @staticmethod
    def lineup_lock_alert(team_id: str, hours_until_lock: int) -> Alert:
        """Create lineup lock reminder"""
        manager = AlertManager()
        
        severity = AlertSeverity.CRITICAL if hours_until_lock < 4 else AlertSeverity.MEDIUM
        
        return manager.create_alert(
            team_id=team_id,
            alert_type=AlertType.LINEUP_LOCK,
            title="⏰ Lineup Lock Coming",
            message=f"Lineup will lock in {hours_until_lock} hours. Make final changes now!",
            severity=severity,
            expires_in_hours=max(1, hours_until_lock),
        )
    
    @staticmethod
    def trade_opportunity_alert(
        team_id: str,
        trade_out: Dict,
        trade_in: Dict,
        point_gain: float,
    ) -> Alert:
        """Create trade recommendation alert"""
        manager = AlertManager()
        
        return manager.create_alert(
            team_id=team_id,
            alert_type=AlertType.TRADE_OPPORTUNITY,
            title=f"💱 Trade: {trade_out['name']} → {trade_in['name']}",
            message=f"Recommended trade could gain {point_gain:.1f} expected points.",
            severity=AlertSeverity.MEDIUM,
            player_id=trade_out['id'],
            expires_in_hours=24,
            metadata={
                "trade_out": trade_out,
                "trade_in": trade_in,
                "expected_gain": point_gain,
            },
        )
    
    @staticmethod
    def player_out_alert(
        team_id: str,
        player_id: str,
        player_name: str,
        reason: str,
    ) -> Alert:
        """Create player unavailable alert"""
        manager = AlertManager()
        
        return manager.create_alert(
            team_id=team_id,
            alert_type=AlertType.PLAYER_OUT,
            title=f"⛔ {player_name} Unavailable",
            message=f"{player_name} is unavailable: {reason}",
            severity=AlertSeverity.HIGH,
            player_id=player_id,
            expires_in_hours=48,
            metadata={"reason": reason},
        )


class NotificationService:
    """Send notifications to coaches"""
    
    def __init__(self):
        self.alert_manager = AlertManager()
    
    async def notify_injury(
        self,
        team_id: str,
        player_id: str,
        player_name: str,
        severity: str,
        send_email: bool = True,
        send_sms: bool = False,
    ) -> None:
        """Notify team of player injury"""
        alert = AlertFactory.injury_alert(team_id, player_id, player_name, severity)
        
        logger.info(f"Injury notification: {player_name} to team {team_id}")
        
        if send_email:
            await self._send_email(team_id, alert)
        if send_sms:
            await self._send_sms(team_id, alert)
    
    async def notify_suspension(
        self,
        team_id: str,
        player_id: str,
        player_name: str,
        rounds_out: int,
    ) -> None:
        """Notify team of player suspension"""
        alert = AlertFactory.suspension_alert(team_id, player_id, player_name, rounds_out)
        logger.info(f"Suspension notification: {player_name} suspended for {rounds_out} rounds")
    
    async def notify_trade_opportunity(
        self,
        team_id: str,
        trade_out: Dict,
        trade_in: Dict,
        point_gain: float,
    ) -> None:
        """Notify team of trade opportunity"""
        alert = AlertFactory.trade_opportunity_alert(team_id, trade_out, trade_in, point_gain)
        logger.info(f"Trade alert sent to team {team_id}")
    
    async def _send_email(self, team_id: str, alert: Alert) -> None:
        """Send email notification (stub)"""
        logger.info(f"Email sent to team {team_id}: {alert.title}")
    
    async def _send_sms(self, team_id: str, alert: Alert) -> None:
        """Send SMS notification (stub)"""
        logger.info(f"SMS sent to team {team_id}: {alert.title}")


if __name__ == "__main__":
    manager = AlertManager()
    
    # Example
    alert = manager.create_alert(
        team_id="team_001",
        alert_type=AlertType.INJURY,
        title="Player Injured",
        message="Player X is out for 2 weeks",
        severity=AlertSeverity.HIGH,
    )
    
    print(f"Alert created: {alert.to_dict()}")
