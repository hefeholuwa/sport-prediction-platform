"""Configuration settings for sports prediction platform."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "sports_predictions.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

SUPPORTED_LEAGUES = {
    "E0": {"name": "Premier League", "country": "England", "season": "2324"},
    "SP1": {"name": "La Liga", "country": "Spain", "season": "2324"},
    "I1": {"name": "Serie A", "country": "Italy", "season": "2324"},
    "D1": {"name": "Bundesliga", "country": "Germany", "season": "2324"},
    "F1": {"name": "Ligue 1", "country": "France", "season": "2324"},
}

DEFAULT_TIME_DECAY = 0.0035
MAX_GOALS_MATRIX = 7
