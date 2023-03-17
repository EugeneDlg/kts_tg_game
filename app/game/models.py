import datetime
import dataclasses
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Player:
    user_id: int
    name: str
    last_name: str
    # score: "GameScoreDC"


# @dataclassd
# class GameScoreDC:
#     points: int


@dataclass
class Game:
    id: int
    created_at: datetime
    chat_id: int
    players: list[Player]


class PlayerModel(db):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint('name', 'last_name', name='_name_lastname_uc'),
    )
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    # game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    games = relationship("GameModel", secondary="players_games", back_populates="players")


class GameModel(db):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    chat_id = Column(String, unique=True, nullable=False)
    # player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    players = relationship("PlayerModel", secondary="players_games", back_populates="games")


class PlayerGameModel(db):
    __tablename__ = "players_games"
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)





# class GameScoreModel(db):
#     id = Column(Integer, primary_key=True)
#     player = Column(Integer, ForeignKey("players.user_id", ondelete="CASCADE"), nullable=False)
#     points = Column(Integer, nullable=False)







