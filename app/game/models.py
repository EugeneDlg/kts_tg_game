import datetime
import dataclasses
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Player:
    id: int
    vk_id: int
    name: str
    last_name: str
    # games: list["Game"]
    scores: list["GameScore"]

    def __getitem__(self, item):
        return getattr(self, item)


@dataclass
class GameScore:
    points: int
    games: "Game"


@dataclass
class Game:
    id: int
    created_at: datetime
    chat_id: int
    players: list[Player]

    def __getitem__(self, item):
        return getattr(self, item)


class PlayerModel(db):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint('name', 'last_name', name='_name_lastname_uc'),
    )
    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    games = relationship("GameModel", secondary="game_score", back_populates="players")
    scores = relationship("GameScoreModel", back_populates="players",
                          viewonly=True,  cascade="all, delete")


class GameModel(db):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    chat_id = Column(Integer, unique=True, nullable=False)
    players = relationship("PlayerModel", secondary="game_score", back_populates="games")
    scores = relationship("GameScoreModel", back_populates="games",
                          viewonly=True,  cascade="all, delete")



class GameScoreModel(db):
    __tablename__ = "game_score"
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True)
    points = Column(Integer, nullable=False, default=0)
    players = relationship("PlayerModel", back_populates="scores", viewonly=True)
    games = relationship("GameModel", back_populates="scores", viewonly=True)





# class GameScoreModel(db):
#     id = Column(Integer, primary_key=True)
#     player = Column(Integer, ForeignKey("players.user_id", ondelete="CASCADE"), nullable=False)
#     points = Column(Integer, nullable=False)







