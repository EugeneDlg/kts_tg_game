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
    status = Column(String, nullable=False, default="registered")
    wait_status = Column(String, nullable=False, default="ok")
    my_points = Column(Integer, nullable=False, default=0)
    players_points = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False)
    chat_id = Column(Integer, nullable=False)
    players = relationship("PlayerModel", secondary="game_score", back_populates="games")
    scores = relationship("GameScoreModel", back_populates="games",
                          viewonly=True,  cascade="all, delete")

    def to_dc(self):
        players = []
        for score in self.scores:
            player = score.players
            p = score.points
            s = GameScore(points=p, games=None)
            players.append(Player(id=player.id, vk_id=player.vk_id,
                                  name=player.name, last_name=player.last_name,
                                  scores=[s]))
        return Game(
            id=self.id,
            created_at=self.created_at,
            chat_id=self.chat_id,
            players=players
        )


class GameScoreModel(db):
    __tablename__ = "game_score"
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True)
    points = Column(Integer, nullable=False, default=0)
    players = relationship("PlayerModel", back_populates="scores", viewonly=True)
    games = relationship("GameModel", back_populates="scores", viewonly=True)





