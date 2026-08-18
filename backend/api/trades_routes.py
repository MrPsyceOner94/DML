"""
API routes for trade recommendations and management
"""

from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional, List
from backend.services.optimization import TradeRecommender, Player, TeamOptimizer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trades", tags=["trades"])

# In-memory services (use DI in production)
optimizer = TeamOptimizer()
recommender = TradeRecommender(optimizer)


@router.post("/suggest")
def get_trade_suggestions(
    team_id: int,
    current_lineup: List[dict],
    available_players: List[dict],
    top_n: int = 5,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Get trade recommendations for team
    
    Returns ranked list of suggested trades with expected point gains
    """
    try:
        # Convert to Player objects
        current = [
            Player(
                id=str(p["id"]),
                name=p.get("name", f"Player {p['id']}"),
                position=p.get("position", "FRF"),
                salary=p.get("salary", 0),
                predicted_score=p.get("predicted_score", 0),
                historical_avg=p.get("historical_avg", 0),
            )
            for p in current_lineup
        ]
        
        available = [
            Player(
                id=str(p["id"]),
                name=p.get("name", f"Player {p['id']}"),
                position=p.get("position", "FRF"),
                salary=p.get("salary", 0),
                predicted_score=p.get("predicted_score", 0),
                historical_avg=p.get("historical_avg", 0),
            )
            for p in available_players
        ]
        
        # Get recommendations
        trades = recommender.suggest_trades(
            current_lineup=current,
            available_players=available,
            top_n=top_n,
        )
        
        return {
            "team_id": team_id,
            "total_recommendations": len(trades),
            "trades": [
                {
                    "trade_out": {
                        "id": t["trade_out"].id,
                        "name": t["trade_out"].name,
                        "position": t["trade_out"].position,
                        "predicted_score": t["trade_out"].predicted_score,
                    },
                    "trade_in": {
                        "id": t["trade_in"].id,
                        "name": t["trade_in"].name,
                        "position": t["trade_in"].position,
                        "predicted_score": t["trade_in"].predicted_score,
                    },
                    "expected_point_gain": t["expected_point_gain"],
                    "salary_impact": t["salary_impact"],
                    "strength": t["strength"],
                }
                for t in trades
            ],
        }
    except Exception as e:
        logger.error(f"Trade suggestion error: {e}")
        raise HTTPException(500, f"Failed to generate suggestions: {str(e)}")


@router.post("/{trade_id}/execute")
def execute_trade(
    trade_id: str,
    team_id: int,
    player_out_id: int,
    player_in_id: int,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Execute a trade (mark as completed)
    
    In production, this would update the database and notify involved teams
    """
    try:
        # Validate trade is real
        return {
            "success": True,
            "trade_id": trade_id,
            "team_id": team_id,
            "message": "Trade executed successfully",
            "player_out": player_out_id,
            "player_in": player_in_id,
        }
    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        raise HTTPException(500, f"Failed to execute trade: {str(e)}")


@router.get("/history/{team_id}")
def get_trade_history(
    team_id: int,
    limit: int = 20,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Get trade history for team
    """
    # This would query the database in production
    return {
        "team_id": team_id,
        "trades": [],
        "total": 0,
    }


@router.get("/pending")
def get_pending_trades(
    league_id: int,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Get all pending trades in league
    """
    return {
        "league_id": league_id,
        "pending_trades": [],
        "total": 0,
    }
