"""
Team Selection Optimization Service

Provides team lineup optimization based on:
- Salary cap constraints
- Player predictions
- Historical performance
- Positional requirements
- Trade recommendations
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)


@dataclass
class Player:
    id: str
    name: str
    position: str
    salary: float
    predicted_score: float
    historical_avg: float
    injury_status: str = "available"
    suspension_rounds: int = 0


@dataclass
class OptimizationResult:
    lineup: List[Player]
    total_salary: float
    total_predicted_score: float
    salary_remaining: float
    changes_from_current: Dict[str, str]  # {player_id: "in" | "out"}
    confidence_score: float


class TeamOptimizer:
    """Optimize team lineups within constraints"""
    
    def __init__(self, salary_cap: float = 12_000_000):
        self.salary_cap = salary_cap
        self.min_positions = {
            "FRF": 2,  # Front row forwards
            "SRF": 2,  # Second row forwards
            "HB": 1,   # Hooker/Back
            "HLF": 1,  # Half-backs
            "CTR": 2,  # Centers
            "WG": 2,   # Wings
            "FB": 1,   # Fullback
        }
        self.total_squad_size = 13
    
    def optimize_lineup(
        self,
        available_players: List[Player],
        current_lineup: Optional[List[Player]] = None,
        frozen_players: Optional[List[str]] = None,
    ) -> OptimizationResult:
        """
        Find optimal team lineup given constraints
        
        Args:
            available_players: All available players
            current_lineup: Current team (for change tracking)
            frozen_players: Players that cannot be traded
            
        Returns:
            OptimizationResult with recommended lineup
        """
        frozen_players = frozen_players or []
        current_lineup = current_lineup or []
        
        # Filter available players
        available = [
            p for p in available_players
            if p.injury_status == "available" and p.suspension_rounds == 0
        ]
        
        # Sort by predicted score per salary ratio
        available_sorted = sorted(
            available,
            key=lambda p: p.predicted_score / max(p.salary, 1),
            reverse=True
        )
        
        # Greedy selection with constraint checking
        selected = []
        used_salary = 0
        position_counts = {pos: 0 for pos in self.min_positions}
        
        # First, select frozen players
        frozen_set = set(frozen_players)
        for player in current_lineup:
            if player.id in frozen_set:
                selected.append(player)
                used_salary += player.salary
                position_counts[player.position] += 1
        
        # Then greedily add best value players
        for player in available_sorted:
            if len(selected) >= self.total_squad_size:
                break
            
            if player.id in frozen_set:
                continue
            
            # Check salary constraint
            if used_salary + player.salary > self.salary_cap:
                continue
            
            # Check position minimums not exceeded
            if position_counts[player.position] >= self.min_positions.get(player.position, 2):
                continue
            
            selected.append(player)
            used_salary += player.salary
            position_counts[player.position] += 1
        
        # Validate minimum positions met
        for pos, min_count in self.min_positions.items():
            if position_counts.get(pos, 0) < min_count:
                logger.warning(f"Position {pos} below minimum {min_count}")
        
        # Calculate changes from current
        current_ids = {p.id for p in current_lineup}
        selected_ids = {p.id for p in selected}
        changes = {}
        for pid in current_ids - selected_ids:
            changes[pid] = "out"
        for pid in selected_ids - current_ids:
            changes[pid] = "in"
        
        # Calculate confidence (based on prediction variance)
        predicted_scores = np.array([p.predicted_score for p in selected])
        confidence = 1.0 - (np.std(predicted_scores) / (np.mean(predicted_scores) + 1))
        confidence = max(0.0, min(1.0, confidence))
        
        return OptimizationResult(
            lineup=selected,
            total_salary=used_salary,
            total_predicted_score=sum(p.predicted_score for p in selected),
            salary_remaining=self.salary_cap - used_salary,
            changes_from_current=changes,
            confidence_score=confidence,
        )
    
    def compare_lineups(
        self,
        lineup_a: List[Player],
        lineup_b: List[Player],
    ) -> Dict:
        """Compare two lineups"""
        score_diff = (
            sum(p.predicted_score for p in lineup_b) -
            sum(p.predicted_score for p in lineup_a)
        )
        salary_diff = (
            sum(p.salary for p in lineup_b) -
            sum(p.salary for p in lineup_a)
        )
        
        # Players in B not in A (trades in)
        a_ids = {p.id for p in lineup_a}
        b_ids = {p.id for p in lineup_b}
        
        return {
            "lineup_a_score": sum(p.predicted_score for p in lineup_a),
            "lineup_b_score": sum(p.predicted_score for p in lineup_b),
            "score_difference": score_diff,
            "salary_difference": salary_diff,
            "players_added": [p for p in lineup_b if p.id not in a_ids],
            "players_removed": [p for p in lineup_a if p.id not in b_ids],
            "better_lineup": "B" if score_diff > 0 else "A",
        }


class TradeRecommender:
    """Generate trade recommendations"""
    
    def __init__(self, optimizer: TeamOptimizer):
        self.optimizer = optimizer
    
    def suggest_trades(
        self,
        current_lineup: List[Player],
        available_players: List[Player],
        top_n: int = 5,
    ) -> List[Dict]:
        """
        Suggest trades to improve team
        
        Returns:
            List of trade recommendations ranked by expected point gain
        """
        recommendations = []
        
        for to_trade in current_lineup:
            for available in available_players:
                # Skip if same position/value not clear
                if to_trade.position != available.position:
                    continue
                
                # Skip if available is not clearly better
                score_gain = available.predicted_score - to_trade.predicted_score
                if score_gain <= 0:
                    continue
                
                # Skip if salary makes it impossible
                salary_diff = available.salary - to_trade.salary
                if salary_diff > self.optimizer.salary_cap * 0.05:  # More than 5% of cap
                    continue
                
                recommendations.append({
                    "trade_out": to_trade,
                    "trade_in": available,
                    "expected_point_gain": score_gain,
                    "salary_impact": salary_diff,
                    "strength": self._calc_trade_strength(score_gain, salary_diff),
                })
        
        # Sort by expected gain
        recommendations.sort(
            key=lambda x: x["expected_point_gain"],
            reverse=True
        )
        
        return recommendations[:top_n]
    
    @staticmethod
    def _calc_trade_strength(score_gain: float, salary_impact: float) -> str:
        """Calculate trade strength rating"""
        if score_gain > 30 and salary_impact < 0:
            return "STRONG_BUY"
        elif score_gain > 15 and salary_impact < 100_000:
            return "BUY"
        elif score_gain > 5:
            return "MODERATE"
        return "PASS"


if __name__ == "__main__":
    # Example usage
    optimizer = TeamOptimizer(salary_cap=12_000_000)
    
    sample_players = [
        Player("p1", "Player 1", "FRF", 800_000, 45.5, 40.2),
        Player("p2", "Player 2", "CTR", 950_000, 52.3, 48.1),
        Player("p3", "Player 3", "WG", 750_000, 38.2, 35.5),
    ]
    
    result = optimizer.optimize_lineup(sample_players)
    print(f"Optimized Score: {result.total_predicted_score}")
    print(f"Salary Used: ${result.total_salary:,}")
