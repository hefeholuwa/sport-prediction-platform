import io
import httpx
import pandas as pd
from typing import Optional
from app.config import SUPPORTED_LEAGUES

class HistoricalDataLoader:
    BASE_URL = "https://www.football-data.co.uk/mmz4281"

    @classmethod
    async def fetch_league_csv(cls, league_code: str, season: str = "2324") -> pd.DataFrame:
        """Download season CSV file from football-data.co.uk."""
        url = f"{cls.BASE_URL}/{season}/{league_code}.csv"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
            return cls.clean_dataframe(df, league_code)

    @staticmethod
    def clean_dataframe(df: pd.DataFrame, league_code: str) -> pd.DataFrame:
        """Standardize columns and filter out unplayed matches."""
        required = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column {col} in CSV for {league_code}")

        df = df.dropna(subset=['FTHG', 'FTAG', 'FTR']).copy()
        df['FTHG'] = df['FTHG'].astype(int)
        df['FTAG'] = df['FTAG'].astype(int)
        
        # Standardize odds with fallbacks
        df['OddsH'] = df['B365H'] if 'B365H' in df.columns else (df['AvgH'] if 'AvgH' in df.columns else 2.0)
        df['OddsD'] = df['B365D'] if 'B365D' in df.columns else (df['AvgD'] if 'AvgD' in df.columns else 3.2)
        df['OddsA'] = df['B365A'] if 'B365A' in df.columns else (df['AvgA'] if 'AvgA' in df.columns else 3.5)
        
        return df
