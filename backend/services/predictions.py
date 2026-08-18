"""
Player Performance Prediction Service

ML models for predicting fantasy points based on:
- Historical performance
- Team form
- Opponent strength
- Rest days
- Positional factors
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PlayerStats:
    player_id: str
    round_num: int
    position: str
    fantasy_points: float
    minutes_played: int
    touches: int
    tackles: int
    offloads: int
    errors: int
    date: datetime


@dataclass
class PredictionResult:
    player_id: str
    predicted_points: float
    confidence: float
    factors: Dict[str, float]  # Impact of each factor
    historical_avg: float
    variance: float


class PlayerPredictor:
    """Predict player fantasy points"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.min_historical_games = 5
    
    def train_model(self, historical_data: List[Dict]) -> bool:
        """
        Train prediction model on historical data
        
        Args:
            historical_data: List of player stats dictionaries
            
        Returns:
            True if training successful
        """
        if len(historical_data) < 100:
            logger.warning(f"Insufficient data for training: {len(historical_data)} samples")
            return False
        
        try:
            # Prepare features and labels
            X = []
            y = []
            
            for record in historical_data:
                features = self._extract_features(record)
                X.append(features)
                y.append(record.get("fantasy_points", 0))
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train ensemble model
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
            )
            self.model.fit(X_scaled, y)
            
            self.is_trained = True
            logger.info("Model training completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return False
    
    def predict(
        self,
        player_id: str,
        position: str,
        historical_games: List[PlayerStats],
        team_form: float,  # 0-1 scale
        opponent_strength: float,  # 0-1 scale
        rest_days: int,
    ) -> Optional[PredictionResult]:
        """
        Predict player fantasy points for next game
        
        Args:
            player_id: Player ID
            position: Player position
            historical_games: Previous game stats (last 10-20 games)
            team_form: Team form factor (0-1)
            opponent_strength: Opponent strength (0-1)
            rest_days: Days since last game
            
        Returns:
            PredictionResult or None if insufficient data
        """
        if len(historical_games) < self.min_historical_games:
            logger.warning(f"Insufficient history for {player_id}: {len(historical_games)} games")
            return None
        
        # Calculate historical stats
        historical_avg = np.mean([g.fantasy_points for g in historical_games])
        historical_std = np.std([g.fantasy_points for g in historical_games])
        
        try:
            # Prepare features
            features = np.array([self._extract_features_from_games(
                position=position,
                historical_games=historical_games,
                team_form=team_form,
                opponent_strength=opponent_strength,
                rest_days=rest_days,
            )])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get prediction
            if self.is_trained and self.model:
                predicted_points = self.model.predict(features_scaled)[0]
            else:
                # Fallback to historical average with form adjustment
                predicted_points = historical_avg * (0.5 + team_form * 0.5)
            
            # Ensure positive prediction
            predicted_points = max(0, predicted_points)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                historical_games=historical_games,
                prediction=predicted_points,
                historical_avg=historical_avg,
            )
            
            # Calculate feature impacts
            factors = self._calculate_feature_impacts(
                position=position,
                team_form=team_form,
                opponent_strength=opponent_strength,
                rest_days=rest_days,
                historical_avg=historical_avg,
            )
            
            return PredictionResult(
                player_id=player_id,
                predicted_points=round(predicted_points, 1),
                confidence=round(confidence, 2),
                factors=factors,
                historical_avg=round(historical_avg, 1),
                variance=round(historical_std, 1),
            )
            
        except Exception as e:
            logger.error(f"Prediction failed for {player_id}: {e}")
            return None
    
    @staticmethod
    def _extract_features(record: Dict) -> List[float]:
        """Extract ML features from a record"""
        return [
            record.get("minutes_played", 0) / 80,  # Normalize to game length
            record.get("touches", 0) / 100,
            record.get("tackles", 0) / 20,
            record.get("offloads", 0) / 10,
            record.get("errors", 0) / 5,
            record.get("fantasy_points", 0) / 100,
        ]
    
    @staticmethod
    def _extract_features_from_games(
        position: str,
        historical_games: List[PlayerStats],
        team_form: float,
        opponent_strength: float,
        rest_days: int,
    ) -> List[float]:
        """Extract features for prediction"""
        avg_minutes = np.mean([g.minutes_played for g in historical_games])
        avg_touches = np.mean([g.touches for g in historical_games])
        avg_tackles = np.mean([g.tackles for g in historical_games])
        avg_points = np.mean([g.fantasy_points for g in historical_games])
        
        # Rest factor (optimal ~2-3 days)
        rest_factor = 1.0 if rest_days in [2, 3] else max(0.7, 1.0 - abs(rest_days - 2.5) * 0.1)
        
        # Position weighting
        position_weight = {
            "FRF": 1.2,  # Front-rowers score more
            "CTR": 1.15,  # Centers higher value
            "WG": 1.0,
            "FB": 1.1,
        }.get(position, 1.0)
        
        return [
            avg_minutes / 80,
            avg_touches / 100,
            avg_tackles / 20,
            avg_points / 100,
            team_form,
            1.0 - opponent_strength,  # Inverse: better if facing weak team
            rest_factor,
            position_weight,
        ]
    
    @staticmethod
    def _calculate_confidence(
        historical_games: List[PlayerStats],
        prediction: float,
        historical_avg: float,
    ) -> float:
        """Calculate prediction confidence (0-1)"""
        if len(historical_games) < 5:
            return 0.5
        
        # Higher confidence if:
        # 1. Consistent performance (low variance)
        # 2. Prediction close to historical average
        # 3. Sufficient history
        
        std = np.std([g.fantasy_points for g in historical_games])
        num_games = min(len(historical_games), 20)  # Cap at 20 games
        
        consistency = 1.0 / (1.0 + std / (historical_avg + 1))
        recency = num_games / 20.0
        prediction_proximity = 1.0 - abs(prediction - historical_avg) / (historical_avg + 1)
        
        confidence = (consistency + recency + prediction_proximity) / 3.0
        return min(1.0, max(0.0, confidence))
    
    @staticmethod
    def _calculate_feature_impacts(
        position: str,
        team_form: float,
        opponent_strength: float,
        rest_days: int,
        historical_avg: float,
    ) -> Dict[str, float]:
        """Calculate impact of each factor on prediction"""
        return {
            "position_effect": (1.0 if position in ["FRF", "CTR"] else 0.0) * 2,
            "team_form": (team_form - 0.5) * historical_avg * 0.3,
            "opponent_strength": (0.5 - opponent_strength) * historical_avg * 0.2,
            "rest_factor": (-abs(rest_days - 2.5) * 0.5 if rest_days > 1 else -5),
            "historical_baseline": historical_avg,
        }


class FormTracker:
    """Track team and player form"""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
    
    def calculate_team_form(self, recent_scores: List[float]) -> float:
        """
        Calculate team form as 0-1 value
        
        Args:
            recent_scores: List of team scores from recent games
            
        Returns:
            Form factor (0=bad form, 1=excellent form)
        """
        if not recent_scores:
            return 0.5
        
        recent = recent_scores[-self.window_size:]
        avg_score = np.mean(recent)
        overall_avg = np.mean(recent_scores)
        
        # Form is ratio of recent to overall
        form = min(1.0, max(0.0, avg_score / (overall_avg + 1)))
        return form
    
    def calculate_player_form(self, recent_games: List[PlayerStats]) -> float:
        """Calculate individual player form"""
        if not recent_games:
            return 0.5
        
        recent = recent_games[-self.window_size:]
        avg_points = np.mean([g.fantasy_points for g in recent])
        overall_avg = np.mean([g.fantasy_points for g in recent_games])
        
        form = min(1.0, max(0.0, avg_points / (overall_avg + 1)))
        return form


if __name__ == "__main__":
    # Example usage
    predictor = PlayerPredictor()
    
    # Mock historical data
    sample_data = [
        {
            "minutes_played": 70 + np.random.randint(-10, 10),
            "touches": 80 + np.random.randint(-20, 20),
            "tackles": 15 + np.random.randint(-5, 5),
            "offloads": 5 + np.random.randint(-2, 2),
            "errors": 2 + np.random.randint(-1, 1),
            "fantasy_points": 45 + np.random.randint(-10, 10),
        }
        for _ in range(200)
    ]
    
    predictor.train_model(sample_data)
    print("Model trained successfully" if predictor.is_trained else "Training failed")
