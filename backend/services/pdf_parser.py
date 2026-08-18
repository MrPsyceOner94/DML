"""
PDF Parser for NRL Fantasy League exports

Extracts league data from PDF exports:
- Team standings
- Player rosters
- Fixtures and results
- Round-by-round scoring
"""

import PyPDF2
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFLeagueParser:
    """Parse NRL Fantasy PDF exports"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.text = self._extract_text()
    
    def _extract_text(self) -> str:
        """Extract all text from PDF"""
        try:
            with open(self.pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_standings(self) -> List[Dict]:
        """
        Extract league standings from PDF
        
        Returns:
            List of teams with rank, points, manager info
        """
        standings = []
        
        # Pattern to match standings table rows
        # Looks for: Rank | Team Name | Manager | Points | PF | PA | Diff
        pattern = r"(\d+)\s+([A-Za-z\s]+)\s+([A-Za-z\s]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([-\d]+)"
        
        matches = re.finditer(pattern, self.text)
        
        for match in matches:
            try:
                standing = {
                    "rank": int(match.group(1)),
                    "team_name": match.group(2).strip(),
                    "manager": match.group(3).strip(),
                    "league_points": int(match.group(4)),
                    "points_for": int(match.group(5)),
                    "points_against": int(match.group(6)),
                    "points_diff": int(match.group(7)),
                }
                standings.append(standing)
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing standing row: {e}")
        
        logger.info(f"Extracted {len(standings)} standings")
        return standings
    
    def extract_rosters(self) -> List[Dict]:
        """
        Extract team rosters from PDF
        
        Returns:
            List of teams with player rosters
        """
        rosters = []
        
        # Split by team sections
        team_pattern = r"Team:\s*([A-Za-z\s]+)\nManager:\s*([A-Za-z\s]+)\n(.+?)(?=Team:|\Z)"
        
        matches = re.finditer(team_pattern, self.text, re.DOTALL)
        
        for match in matches:
            team_name = match.group(1).strip()
            manager = match.group(2).strip()
            roster_text = match.group(3)
            
            # Extract players from roster section
            players = []
            player_pattern = r"(\d+)\s+([A-Za-z\s]+)\s+([A-Z]{2,3})\s+(\d+\.\d+M|\d+K)"
            
            for player_match in re.finditer(player_pattern, roster_text):
                try:
                    player = {
                        "player_id": int(player_match.group(1)),
                        "name": player_match.group(2).strip(),
                        "position": player_match.group(3),
                        "salary": player_match.group(4),
                    }
                    players.append(player)
                except (ValueError, IndexError):
                    continue
            
            if players or team_name:
                roster = {
                    "team_name": team_name,
                    "manager": manager,
                    "players": players,
                    "squad_size": len(players),
                }
                rosters.append(roster)
        
        logger.info(f"Extracted {len(rosters)} team rosters")
        return rosters
    
    def extract_fixtures(self) -> List[Dict]:
        """
        Extract match fixtures from PDF
        
        Returns:
            List of fixtures with results
        """
        fixtures = []
        
        # Pattern to match fixture rows
        # Format: Round X | Team A vs Team B | Score: X-Y | Date
        fixture_pattern = r"Round\s*(\d+).*?([A-Za-z\s]+)\s+vs\s+([A-Za-z\s]+)\s+(\d+)\s*-\s*(\d+).*?(\d{4}-\d{2}-\d{2})"
        
        matches = re.finditer(fixture_pattern, self.text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            try:
                fixture = {
                    "round": int(match.group(1)),
                    "home_team": match.group(2).strip(),
                    "away_team": match.group(3).strip(),
                    "home_score": int(match.group(4)),
                    "away_score": int(match.group(5)),
                    "date": match.group(6),
                    "finished": True,
                }
                fixtures.append(fixture)
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing fixture: {e}")
        
        logger.info(f"Extracted {len(fixtures)} fixtures")
        return fixtures
    
    def extract_round_history(self) -> List[Dict]:
        """
        Extract round-by-round history for teams
        
        Returns:
            List of round results with team scores
        """
        history = []
        
        # Pattern for round results
        round_pattern = r"Round\s*(\d+).*?Teams:\s*(.+?)\n(.+?)(?=Round|\Z)"
        
        matches = re.finditer(round_pattern, self.text, re.DOTALL)
        
        for match in matches:
            try:
                round_num = int(match.group(1))
                results_text = match.group(3)
                
                # Extract individual team scores
                score_pattern = r"([A-Za-z\s]+):\s*(\d+)\s*pts"
                scores = []
                
                for score_match in re.finditer(score_pattern, results_text):
                    scores.append({
                        "team": score_match.group(1).strip(),
                        "score": int(score_match.group(2)),
                    })
                
                if scores:
                    history.append({
                        "round": round_num,
                        "team_scores": scores,
                    })
            
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing round history: {e}")
        
        logger.info(f"Extracted {len(history)} round histories")
        return history
    
    def extract_player_scores(self) -> Dict[int, List[Dict]]:
        """
        Extract player scores by round
        
        Returns:
            Dictionary mapping round to player scores
        """
        scores_by_round = {}
        
        # Pattern to find player score entries
        score_pattern = r"Round\s*(\d+).*?Player:\s*([A-Za-z\s]+)\s+Score:\s*(\d+)\s*pts"
        
        matches = re.finditer(score_pattern, self.text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            try:
                round_num = int(match.group(1))
                player_name = match.group(2).strip()
                score = int(match.group(3))
                
                if round_num not in scores_by_round:
                    scores_by_round[round_num] = []
                
                scores_by_round[round_num].append({
                    "player": player_name,
                    "score": score,
                })
            
            except (ValueError, IndexError):
                continue
        
        logger.info(f"Extracted scores for {len(scores_by_round)} rounds")
        return scores_by_round


def parse_nrl_pdf(pdf_path: str) -> Dict:
    """
    Parse complete NRL Fantasy PDF export
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary with all extracted data
    """
    parser = PDFLeagueParser(pdf_path)
    
    return {
        "source": "pdf_export",
        "file": pdf_path,
        "standings": parser.extract_standings(),
        "rosters": parser.extract_rosters(),
        "fixtures": parser.extract_fixtures(),
        "round_history": parser.extract_round_history(),
        "player_scores": parser.extract_player_scores(),
        "extracted_at": __import__("datetime").datetime.utcnow().isoformat(),
    }
