from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from app.pipeline.sample_data import get_seed_leagues, get_seed_matches

router = APIRouter(prefix="/api", tags=["fixtures"])

@router.get("/leagues", response_model=List[Dict[str, Any]])
def list_leagues() -> List[Dict[str, Any]]:
    """Return supported football leagues."""
    return get_seed_leagues()

@router.get("/fixtures", response_model=List[Dict[str, Any]])
def list_fixtures(league_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Return upcoming scheduled fixtures with optional league filtering."""
    matches = get_seed_matches()
    if league_id:
        norm_league = league_id.upper().strip()
        if norm_league != "ALL":
            matches = [m for m in matches if m["league_id"].upper() == norm_league]
    return matches
