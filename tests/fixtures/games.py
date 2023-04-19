import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.game.models import Game, GameModel, PlayerModel, Player, QuestionModel, AnswerModel


@pytest.fixture
async def game_1(db_session: AsyncSession) -> Game:
    chat_id = 111
    created_at = datetime.datetime.now()
    status = "registered"
    wait_status = "ok"
    wait_time = 0
    my_points = 0
    players_points = 0
    round_ = 0
    blitz_round = 0
    current_question_id = None
    player_id = 1
    vk_id = 777
    name = "Fuf"
    last_name = "Poop"
    scores = None
    new_players = [PlayerModel(vk_id=vk_id, name=name, last_name=last_name)]
    new_players_dc = [Player(id=player_id, vk_id=vk_id,
                             name=name, last_name=last_name, scores=scores)]
    game = GameModel(
        chat_id=chat_id, captain=[], created_at=created_at, players=new_players
    )
    async with db_session.begin() as session:
        session.add(game)
    return Game(
        id=1,
        chat_id=chat_id,
        created_at=created_at,
        status=status,
        wait_status=wait_status,
        wait_time=wait_time,
        round=round_,
        blitz_round=blitz_round,
        current_question_id=current_question_id,
        my_points=my_points,
        players_points=players_points,
        captain=[],
        speaker=[],
        players=new_players_dc,
    )


@pytest.fixture
async def game_2(db_session: AsyncSession) -> Game:
    chat_id = 222
    created_at = datetime.datetime.now()
    status = "registered"
    wait_status = "ok"
    wait_time = 0
    my_points = 0
    players_points = 0
    round_ = 0
    blitz_round = 0
    current_question_id = None
    player_id = 1
    vk_id = 888
    name = "Fufy"
    last_name = "Poopy"
    scores = None
    new_players = [PlayerModel(vk_id=vk_id, name=name, last_name=last_name)]
    new_players_dc = [Player(id=player_id, vk_id=vk_id,
                             name=name, last_name=last_name, scores=scores)]
    game = GameModel(
        chat_id=chat_id, captain=[], created_at=created_at, players=new_players
    )
    async with db_session.begin() as session:
        session.add(game)
    return Game(
        id=1,
        chat_id=chat_id,
        created_at=created_at,
        status=status,
        wait_status=wait_status,
        wait_time=wait_time,
        round=round_,
        blitz_round=blitz_round,
        current_question_id=current_question_id,
        my_points=my_points,
        players_points=players_points,
        captain=[],
        speaker=[],
        players=new_players_dc,
    )


@pytest.fixture
async def game_1(db_session: AsyncSession) -> Game:
    chat_id = 111
    created_at = datetime.datetime.now()
    status = "registered"
    wait_status = "ok"
    wait_time = 0
    my_points = 0
    players_points = 0
    round_ = 0
    blitz_round = 0
    current_question_id = None
    player_id = 1
    vk_id = 777
    name = "Fuf"
    last_name = "Poop"
    scores = None
    new_players = [PlayerModel(vk_id=vk_id, name=name, last_name=last_name)]
    new_players_dc = [Player(id=player_id, vk_id=vk_id,
                             name=name, last_name=last_name, scores=scores)]
    game = GameModel(
        chat_id=chat_id, captain=[], created_at=created_at, players=new_players
    )
    async with db_session.begin() as session:
        session.add(game)
    return Game(
        id=1,
        chat_id=chat_id,
        created_at=created_at,
        status=status,
        wait_status=wait_status,
        wait_time=wait_time,
        round=round_,
        blitz_round=blitz_round,
        current_question_id=current_question_id,
        my_points=my_points,
        players_points=players_points,
        captain=[],
        speaker=[],
        players=new_players_dc,
    )


@pytest.fixture
async def create_question_1(db_session: AsyncSession, question_1) -> Game:
    question = question_1
    async with db_session.begin() as session:
        session.add(question)
    return question


@pytest.fixture
async def question_1(answer_1):
    text = "This a question number 1"
    blitz = False
    question = QuestionModel(text=text, blitz=blitz, answer=[answer_1])
    return question


@pytest.fixture
def answer_1():
    text = "This is an answer foe question number 1"
    return AnswerModel(text=text)