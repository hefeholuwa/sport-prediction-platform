import io
import httpx
import pandas as pd

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
        """Standardize columns and filter out unplayed matches with robust odds fallbacks."""
        required = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column {col} in CSV for {league_code}")

        df = df.dropna(subset=['FTHG', 'FTAG', 'FTR']).copy()
        df['FTHG'] = df['FTHG'].astype(int)
        df['FTAG'] = df['FTAG'].astype(int)
        
        # Row-level odds fallback with combine_first and fillna
        def extract_odds(primary_col: str, secondary_col: str, default_val: float) -> pd.Series:
            s_primary = pd.to_numeric(df[primary_col], errors='coerce') if primary_col in df.columns else pd.Series(index=df.index, dtype=float)
            s_secondary = pd.to_numeric(df[secondary_col], errors='coerce') if secondary_col in df.columns else pd.Series(index=df.index, dtype=float)
            return s_primary.combine_first(s_secondary).fillna(default_val)

        df['OddsH'] = extract_odds('B365H', 'AvgH', 2.0)
        df['OddsD'] = extract_odds('B365D', 'AvgD', 3.2)
        df['OddsA'] = extract_odds('B365A', 'AvgA', 3.5)
        
        return df

