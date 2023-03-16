import datetime
import dataclasses
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass()
class PlayerDC:
    user_id: int
    name: str
    last_name: str
    score: "GameScoreDC"


@dataclass()
class GameScoreDC:
    points: int


@dataclass()
class GameDC:
    id: int
    created_at: datetime
    chat_id: int
    players: list[PlayerDC]


class PlayerModel(db):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint('name', 'last_name', name='_name_lastname_uc'),
    )
    user_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    game = Column(Integer, ForeignKey("game.id_", ondelete="CASCADE"), nullable=False)


class GameScoreModel(db):
    id_ = Column(Integer, primary_key=True)
    player = Column(Integer, ForeignKey("players.user_id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False)


class Game(db):
    id_ = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    chat_id = Column(String, unique=True, nullable=False)
    # answers = relationship("AnswerModel", back_populates="questions", cascade="all, delete")
    ### to continue




