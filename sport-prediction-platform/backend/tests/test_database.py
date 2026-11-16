import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.schema import Base, League, Team, Match, Prediction
from app.database import get_db

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

    team = Team(name="Arsenal", league_id="E0", attack_rating=1.45, defense_rating=0.85)
    session.add(team)
    session.commit()
    assert team.league.name == "Premier League"
    assert len(saved_league.teams) == 1

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
    assert saved_match.league.id == "E0"

    prediction = Prediction(
        match_id=saved_match.id,
        home_win_prob=0.55,
        draw_prob=0.25,
        away_win_prob=0.20,
        over_2_5_prob=0.58,
        under_2_5_prob=0.42,
        btts_yes_prob=0.52,
        btts_no_prob=0.48,
        home_xg=1.85,
        away_xg=0.95,
        predicted_score="2-1",
        score_matrix_json="[[0.1]]"
    )
    session.add(prediction)
    session.commit()

    assert saved_match.prediction is not None
    assert saved_match.prediction.predicted_score == "2-1"
    assert prediction.match.home_team == "Arsenal"

def test_get_db_generator():
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    try:
        next(db_gen)
    except StopIteration:
        pass  # Clean closure

