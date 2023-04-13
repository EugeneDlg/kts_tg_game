import datetime
import uuid
from dataclasses import dataclass

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db.sqlalchemy_base import db


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
    chat_id: int
    created_at: datetime
    speaker: list[Player]
    captain: list[Player]
    players: list[Player]
    current_question_id: str
    wait_status: str = "ok"
    wait_time: int = 0
    status: str = "registered"
    my_points: int = 0
    players_points: int = 0
    round: int = 0
    blitz_round: int = 0

    def __getitem__(self, item):
        return getattr(self, item)


@dataclass
class Question:
    id: str
    text: str
    answer: list["Answer"]
    blitz: bool = False
    current_game: list[Game] = None


@dataclass
class Answer:
    id: str
    text: str
    question_id: str


class PlayerModel(db):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("name", "last_name", name="_name_lastname_uc"),
    )
    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    game_captain = relationship(
        "GameModel", secondary="game_captains", back_populates="captain"
    )
    game_speaker = relationship(
        "GameModel", secondary="game_speakers", back_populates="speaker"
    )
    games = relationship(
        "GameModel", secondary="game_score", back_populates="players"
    )
    scores = relationship(
        "GameScoreModel",
        back_populates="players",
        viewonly=True,
        cascade="all, delete",
    )


class GameModel(db):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="registered")
    wait_status = Column(String, nullable=False, default="ok")
    wait_time = Column(Integer, nullable=False, default=0)
    my_points = Column(Integer, nullable=False, default=0)
    players_points = Column(Integer, nullable=False, default=0)
    round = Column(Integer, nullable=False, default=0)
    blitz_round = Column(Integer, nullable=False, default=0)
    current_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    created_at = Column(DateTime, nullable=False)

    speaker = relationship(
        "PlayerModel", secondary="game_speakers", back_populates="game_speaker"
    )
    questions = relationship(
        "QuestionModel", secondary="used_questions", back_populates="games"
    )
    players = relationship(
        "PlayerModel", secondary="game_score", back_populates="games"
    )
    scores = relationship(
        "GameScoreModel",
        back_populates="games",
        viewonly=True,
        cascade="all, delete",
    )
    captain = relationship(
        "PlayerModel", secondary="game_captains", back_populates="game_captain"
    )
    current_question = relationship(
        "QuestionModel", back_populates="current_game"
    )

    # def to_dc(self):
    #     players = []
    #     for score in self.scores:
    #         player = score.players
    #         p = score.points
    #         s = GameScore(points=p, games=None)
    #         players.append(
    #             Player(
    #                 id=player.id,
    #                 vk_id=player.vk_id,
    #                 name=player.name,
    #                 last_name=player.last_name,
    #                 scores=[s],
    #             )
    #         )
    #     return Game(
    #         id=self.id,
    #         created_at=self.created_at,
    #         chat_id=self.chat_id,
    #         players=players,
    #     )


class GameScoreModel(db):
    __tablename__ = "game_score"
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True
    )
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    points = Column(Integer, nullable=False, default=0)
    players = relationship(
        "PlayerModel", back_populates="scores", viewonly=True
    )
    games = relationship("GameModel", back_populates="scores", viewonly=True)


class GameCaptainModel(db):
    __tablename__ = "game_captains"
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"))


class GameSpeakerModel(db):
    __tablename__ = "game_speakers"
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"))


class QuestionModel(db):
    __tablename__ = "questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False, default="", unique=True)
    blitz = Column(Boolean, nullable=False, default=False)
    answer = relationship(
        "AnswerModel", back_populates="question", cascade="all, delete"
    )
    games = relationship(
        "GameModel", secondary="used_questions", back_populates="questions"
    )
    current_game = relationship("GameModel", back_populates="current_question")


class AnswerModel(db):
    __tablename__ = "answers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False, default="")
    question_id = Column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE")
    )
    question = relationship("QuestionModel", back_populates="answer")


class UsedQuestionsModel(db):
    __tablename__ = "used_questions"
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
