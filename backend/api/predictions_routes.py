"""
API routes for player performance predictions
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from backend.services.predictions import PlayerPredictor, PlayerStats, FormTracker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

# In-memory predictor (use DI in production)
predictor = PlayerPredictor()
form_tracker = FormTracker(window_size=5)


@router.post("/train")
def train_predictions(historical_data: List[dict]):
    """
    Train ML prediction model with historical data
    
    Expected format:
    [
        {
            "minutes_played": 70,
            "touches": 85,
            "tackles": 12,
            "offloads": 3,
            "errors": 1,
            "fantasy_points": 45,
        },
        ...
    ]
    """
    try:
        success = predictor.train_model(historical_data)
        return {
            "success": success,
            "model_trained": predictor.is_trained,
            "samples_used": len(historical_data),
            "message": "Model training completed" if success else "Training failed - insufficient data",
        }
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(500, f"Training failed: {str(e)}")


@router.post("/player/{player_id}")
def predict_player(
    player_id: str,
    position: str,
    historical_games: List[dict],
    team_form: float,
    opponent_strength: float,
    rest_days: int,
):
    """
    Predict player fantasy points for next game
    
    Args:
        position: Player position (FRF, CTR, WG, FB, etc.)
        historical_games: List of last games with stats
        team_form: Team form 0-1 (0=poor, 1=excellent)
        opponent_strength: Opponent strength 0-1 (0=weak, 1=strong)
        rest_days: Days since last game
    """
    try:
        # Convert to PlayerStats objects
        games = [
            PlayerStats(
                player_id=player_id,
                round_num=g.get("round", 0),
                position=position,
                fantasy_points=g.get("fantasy_points", 0),
                minutes_played=g.get("minutes_played", 0),
                touches=g.get("touches", 0),
                tackles=g.get("tackles", 0),
                offloads=g.get("offloads", 0),
                errors=g.get("errors", 0),
                date=datetime.fromisoformat(g.get("date", datetime.utcnow().isoformat())),
            )
            for g in historical_games
        ]
        
        # Get prediction
        result = predictor.predict(
            player_id=player_id,
            position=position,
            historical_games=games,
            team_form=team_form,
            opponent_strength=opponent_strength,
            rest_days=rest_days,
        )
        
        if not result:
            raise HTTPException(400, "Insufficient historical data for prediction")
        
        return {
            "player_id": player_id,
            "position": position,
            "predicted_points": result.predicted_points,
            "confidence": result.confidence,
            "historical_avg": result.historical_avg,
            "variance": result.variance,
            "factors": result.factors,
            "input": {
                "team_form": team_form,
                "opponent_strength": opponent_strength,
                "rest_days": rest_days,
            },
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(500, f"Prediction failed: {str(e)}")


@router.get("/team-form/{team_id}")
def get_team_form(
    team_id: int,
    recent_scores: List[float],
    all_scores: Optional[List[float]] = None,
):
    """
    Get team form factor
    
    Args:
        recent_scores: Team scores from recent games
        all_scores: All season scores for baseline
    """
    try:
        all_s = all_scores or recent_scores
        form = form_tracker.calculate_team_form(all_s)
        recent_avg = sum(recent_scores[-5:]) / len(recent_scores[-5:]) if recent_scores else 0
        
        return {
            "team_id": team_id,
            "form": round(form, 2),
            "form_label": (
                "Excellent" if form > 0.8 else
                "Good" if form > 0.6 else
                "Average" if form > 0.4 else
                "Poor"
            ),
            "recent_avg": round(recent_avg, 1),
            "trend": "up" if form > 0.5 else "down",
        }
    except Exception as e:
        logger.error(f"Form calculation error: {e}")
        raise HTTPException(500, f"Form calculation failed: {str(e)}")
