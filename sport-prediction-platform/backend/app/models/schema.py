from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class League(Base):
    __tablename__ = "leagues"

    id = Column(String, primary_key=True)  # e.g., "E0"
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    csv_code = Column(String, nullable=False)

    matches = relationship("Match", back_populates="league")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    attack_rating = Column(Float, default=1.0)
    defense_rating = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    match_date = Column(String, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_goals = Column(Integer, nullable=True)
    away_goals = Column(Integer, nullable=True)
    result = Column(String(1), nullable=True)  # 'H', 'D', 'A'
    odds_home = Column(Float, nullable=True)
    odds_draw = Column(Float, nullable=True)
    odds_away = Column(Float, nullable=True)
    is_finished = Column(Boolean, default=False)

    league = relationship("League", back_populates="matches")
    prediction = relationship("Prediction", back_populates="match", uselist=False)

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    home_win_prob = Column(Float, nullable=False)
    draw_prob = Column(Float, nullable=False)
    away_win_prob = Column(Float, nullable=False)
    over_2_5_prob = Column(Float, nullable=False)
    under_2_5_prob = Column(Float, nullable=False)
    btts_yes_prob = Column(Float, nullable=False)
    btts_no_prob = Column(Float, nullable=False)
    home_xg = Column(Float, nullable=False)
    away_xg = Column(Float, nullable=False)
    predicted_score = Column(String, nullable=False)
    score_matrix_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="prediction")
