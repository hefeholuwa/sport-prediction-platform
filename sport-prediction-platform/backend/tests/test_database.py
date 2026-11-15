import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.schema import Base, League, Team, Match, Prediction

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()

def test_create_and_query_tables(session):
    league = League(id="E0", name="Premier League", country="England", csv_code="E0")
    session.add(league)
    session.commit()
    
    saved_league = session.query(League).filter_by(id="E0").first()
    assert saved_league is not None
    assert saved_league.name == "Premier League"

    match = Match(
        league_id="E0",
        match_date="2026-11-20",
        home_team="Arsenal",
        away_team="Chelsea",
        odds_home=1.85,
        odds_draw=3.60,
        odds_away=4.20,
        is_finished=False
    )
    session.add(match)
    session.commit()

    saved_match = session.query(Match).filter_by(home_team="Arsenal").first()
    assert saved_match.away_team == "Chelsea"
