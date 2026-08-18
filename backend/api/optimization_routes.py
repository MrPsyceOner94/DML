"""
API routes for team optimization endpoints
"""

from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional, List
from backend.services.optimization import TeamOptimizer, Player, TradeRecommender
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimize", tags=["optimize"])

# In-memory optimizer (use DI in production)
optimizer = TeamOptimizer(salary_cap=12_000_000)
recommender = TradeRecommender(optimizer)


@router.post("/team")
def optimize_team(
    team_id: int,
    available_players: List[dict],
    current_lineup: Optional[List[dict]] = None,
    frozen_players: Optional[List[int]] = None,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Get optimized team lineup
    
    Returns best possible team within salary cap constraints
    """
    try:
        # Convert to Player objects
        players = [
            Player(
                id=str(p["id"]),
                name=p.get("name", f"Player {p['id']}"),
                position=p.get("position", "FRF"),
                salary=p.get("salary", 0),
                predicted_score=p.get("predicted_score", 0),
                historical_avg=p.get("historical_avg", 0),
                injury_status=p.get("injury_status", "available"),
                suspension_rounds=p.get("suspension_rounds", 0),
            )
            for p in available_players
        ]
        
        current = [
            Player(
                id=str(p["id"]),
                name=p.get("name", f"Player {p['id']}"),
                position=p.get("position", "FRF"),
                salary=p.get("salary", 0),
                predicted_score=p.get("predicted_score", 0),
                historical_avg=p.get("historical_avg", 0),
            )
            for p in (current_lineup or [])
        ]
        
        # Optimize
        result = optimizer.optimize_lineup(
            available_players=players,
            current_lineup=current,
            frozen_players=frozen_players or [],
        )
        
        return {
            "team_id": team_id,
            "lineup": [
                {
                    "id": p.id,
                    "name": p.name,
                    "position": p.position,
                    "salary": p.salary,
                    "predicted_score": p.predicted_score,
                }
                for p in result.lineup
            ],
            "total_salary": result.total_salary,
            "total_predicted_score": result.total_predicted_score,
            "salary_remaining": result.salary_remaining,
            "changes": result.changes_from_current,
            "confidence": result.confidence_score,
        }
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(500, f"Optimization failed: {str(e)}")


@router.post("/compare")
def compare_lineups(
    lineup_a: List[dict],
    lineup_b: List[dict],
):
    """
    Compare two team lineups
    
    Returns predicted point difference and changes
    """
    try:
        players_a = [
            Player(
                id=str(p["id"]),
                name=p.get("name", f"Player {p['id']}"),
                position=p.get("position", "FRF"),
                salary=p.get("salary", 0),
                predicted_score=p.get("predicted_score", 0),
                historical_avg=p.get("historical_avg", 0),
            )
            for p in lineup_a
        ]
        
        players_b = [
            Player(
                id=str(p["id"]),
                name=p.get("name", f"Player {p['id']}"),
                position=p.get("position", "FRF"),
                salary=p.get("salary", 0),
                predicted_score=p.get("predicted_score", 0),
                historical_avg=p.get("historical_avg", 0),
            )
            for p in lineup_b
        ]
        
        comparison = optimizer.compare_lineups(players_a, players_b)
        
        return {
            "lineup_a_score": comparison["lineup_a_score"],
            "lineup_b_score": comparison["lineup_b_score"],
            "score_difference": comparison["score_difference"],
            "salary_difference": comparison["salary_difference"],
            "players_added": [
                {"id": p.id, "name": p.name, "score": p.predicted_score}
                for p in comparison["players_added"]
            ],
            "players_removed": [
                {"id": p.id, "name": p.name, "score": p.predicted_score}
                for p in comparison["players_removed"]
            ],
            "better_lineup": comparison["better_lineup"],
        }
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(500, f"Comparison failed: {str(e)}")


@router.get("/salary-cap/{team_id}")
def salary_cap_analysis(team_id: int, current_lineup: Optional[List[dict]] = None):
    """
    Analyze team salary cap usage
    """
    players = [
        Player(
            id=str(p["id"]),
            name=p.get("name", f"Player {p['id']}"),
            position=p.get("position", "FRF"),
            salary=p.get("salary", 0),
            predicted_score=p.get("predicted_score", 0),
            historical_avg=p.get("historical_avg", 0),
        )
        for p in (current_lineup or [])
    ]
    
    total_salary = sum(p.salary for p in players)
    used_pct = (total_salary / optimizer.salary_cap) * 100
    
    return {
        "team_id": team_id,
        "salary_cap": optimizer.salary_cap,
        "total_used": total_salary,
        "remaining": optimizer.salary_cap - total_salary,
        "usage_percent": round(used_pct, 1),
        "players_count": len(players),
        "avg_salary_per_player": round(total_salary / len(players), 0) if players else 0,
    }
