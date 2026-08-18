"""
API endpoints for NRL Fantasy data extraction and management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
from typing import Optional
import logging
import asyncio
from datetime import datetime
from backend.services.nrl_data_extractor import (
    NRLFantasyExtractor,
    NRLFantasyDataProcessor,
    extract_all_nrl_data,
)
from backend.services.pdf_parser import PDFLeagueParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])

# Track extraction status
extraction_status = {
    "status": "idle",
    "progress": 0,
    "current_task": None,
    "last_extraction": None,
    "error": None,
}


@router.post("/extract/league/{league_id}")
async def extract_league_data(
    league_id: int = 60018,
    background_tasks: BackgroundTasks = None,
):
    """
    Extract all NRL Fantasy data for a league
    
    Runs in background and extracts:
    - Teams & managers
    - All players
    - Player scores by round
    - Fixtures & results
    - Current standings
    - Injuries & suspensions
    """
    global extraction_status
    
    if extraction_status["status"] == "extracting":
        raise HTTPException(409, "Extraction already in progress")
    
    extraction_status["status"] = "extracting"
    extraction_status["current_task"] = f"Extracting data for league {league_id}"
    extraction_status["progress"] = 0
    extraction_status["error"] = None
    
    # Run extraction in background
    if background_tasks:
        background_tasks.add_task(
            _run_extraction,
            league_id=league_id,
        )
    
    return {
        "status": "started",
        "league_id": league_id,
        "message": "Data extraction started in background",
    }


async def _run_extraction(league_id: int):
    """Background task to extract data"""
    global extraction_status
    
    try:
        extraction_status["current_task"] = "Connecting to NRL Fantasy API..."
        extraction_status["progress"] = 10
        
        data = await extract_all_nrl_data(league_id=league_id, save=True)
        
        extraction_status["status"] = "completed"
        extraction_status["progress"] = 100
        extraction_status["last_extraction"] = datetime.utcnow().isoformat()
        extraction_status["current_task"] = "Extraction completed"
        
        logger.info(f"Successfully extracted data for league {league_id}")
    
    except Exception as e:
        extraction_status["status"] = "failed"
        extraction_status["error"] = str(e)
        logger.error(f"Extraction failed: {e}")
    
    finally:
        extraction_status["status"] = "idle"


@router.get("/extraction-status")
def get_extraction_status():
    """
    Get current status of data extraction
    """
    return extraction_status


@router.post("/upload-pdf")
async def upload_pdf_data(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """
    Upload NRL Fantasy PDF export and extract league data
    
    Parses PDF to extract:
    - Teams and standings
    - Current rosters
    - Historical scores
    - Fixtures
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")
    
    global extraction_status
    
    extraction_status["status"] = "processing"
    extraction_status["current_task"] = f"Processing PDF: {file.filename}"
    extraction_status["progress"] = 0
    
    try:
        # Read PDF file
        contents = await file.read()
        
        # Parse PDF in background
        if background_tasks:
            background_tasks.add_task(
                _process_pdf,
                pdf_content=contents,
                filename=file.filename,
            )
        
        return {
            "status": "processing",
            "filename": file.filename,
            "message": "PDF processing started",
        }
    
    except Exception as e:
        extraction_status["status"] = "idle"
        extraction_status["error"] = str(e)
        raise HTTPException(500, f"PDF processing failed: {str(e)}")


async def _process_pdf(pdf_content: bytes, filename: str):
    """Background task to process PDF"""
    global extraction_status
    
    try:
        extraction_status["current_task"] = "Parsing PDF..."
        extraction_status["progress"] = 20
        
        # Save PDF temporarily
        pdf_path = f"/tmp/{filename}"
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)
        
        # Parse PDF
        parser = PDFLeagueParser(pdf_path)
        
        extraction_status["current_task"] = "Extracting standings..."
        extraction_status["progress"] = 40
        standings = parser.extract_standings()
        
        extraction_status["current_task"] = "Extracting rosters..."
        extraction_status["progress"] = 60
        rosters = parser.extract_rosters()
        
        extraction_status["current_task"] = "Extracting fixtures..."
        extraction_status["progress"] = 80
        fixtures = parser.extract_fixtures()
        
        # Save processed data
        processor = NRLFantasyDataProcessor()
        data = {
            "source": "pdf_upload",
            "filename": filename,
            "standings": standings,
            "rosters": rosters,
            "fixtures": fixtures,
            "extracted_at": datetime.utcnow().isoformat(),
        }
        processor.save_league_data(data, "league_pdf_extract.json")
        
        extraction_status["status"] = "completed"
        extraction_status["progress"] = 100
        extraction_status["last_extraction"] = datetime.utcnow().isoformat()
        extraction_status["current_task"] = "PDF extraction completed"
        
        logger.info(f"Successfully processed PDF: {filename}")
    
    except Exception as e:
        extraction_status["status"] = "failed"
        extraction_status["error"] = str(e)
        logger.error(f"PDF processing failed: {e}")
    
    finally:
        extraction_status["status"] = "idle"


@router.get("/league/{league_id}/summary")
async def get_league_summary(league_id: int = 60018):
    """
    Get summary of extracted league data
    """
    processor = NRLFantasyDataProcessor()
    
    try:
        # Load extracted data
        with open(f"data/nrl_fantasy_dml.json", "r") as f:
            import json
            data = json.load(f)
        
        return {
            "league_id": league_id,
            "league_name": data["league"].get("name"),
            "season": data["league"].get("season"),
            "current_round": data["league"].get("current_round"),
            "teams": {
                "total": len(data["teams"]),
                "sample": data["teams"][:3],
            },
            "players": {
                "total": len(data["players"]),
                "available": len([p for p in data["players"] if p["status"] == "available"]),
                "injured": len([p for p in data["players"] if p["injury_status"] == "out"]),
            },
            "fixtures": {
                "total": len(data["fixtures"]),
                "completed": len([f for f in data["fixtures"] if f["finished"]]),
                "upcoming": len([f for f in data["fixtures"] if not f["finished"]]),
            },
            "unavailable_players": len(data["injuries_suspensions"]),
            "extracted_at": data["processed_at"],
        }
    
    except FileNotFoundError:
        raise HTTPException(404, "League data not found. Run extraction first.")
    except Exception as e:
        raise HTTPException(500, f"Error loading league data: {str(e)}")


@router.get("/players/injuries")
async def get_injured_players(league_id: int = 60018):
    """
    Get all injured/suspended players with severity levels
    """
    try:
        with open(f"data/nrl_fantasy_dml.json", "r") as f:
            import json
            data = json.load(f)
        
        injuries = data["injuries_suspensions"]
        
        # Group by severity
        by_severity = {
            "critical": [p for p in injuries if p["severity"] == "critical"],
            "major": [p for p in injuries if p["severity"] == "major"],
            "minor": [p for p in injuries if p["severity"] == "minor"],
        }
        
        return {
            "total": len(injuries),
            "by_severity": by_severity,
            "last_updated": data["processed_at"],
        }
    
    except FileNotFoundError:
        raise HTTPException(404, "Injury data not found")


@router.get("/standings")
async def get_standings(league_id: int = 60018, round_num: Optional[int] = None):
    """
    Get league standings for a specific round
    """
    try:
        with open(f"data/nrl_fantasy_dml.json", "r") as f:
            import json
            data = json.load(f)
        
        standings = data["standings"]
        
        # Sort by rank
        standings_sorted = sorted(standings, key=lambda x: x["rank"])
        
        return {
            "league_id": league_id,
            "round": round_num or data["league"].get("current_round"),
            "standings": standings_sorted,
            "total_teams": len(standings_sorted),
        }
    
    except FileNotFoundError:
        raise HTTPException(404, "Standings data not found")
