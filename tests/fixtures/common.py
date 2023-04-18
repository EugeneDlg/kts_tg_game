import datetime
import logging
import os
from hashlib import sha256
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import TestClient, loop_context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.admin.models import Admin, AdminModel
from apps.admin.accessor.accessor import AdminAccessor
from apps.api.app import setup_app
from apps.game.models import Game, GameModel, PlayerModel, Player, AnswerModel
from config.config import Config
from db.database import Database


@pytest.fixture(scope="session")
def event_loop():
    with loop_context() as _loop:
        yield _loop


@pytest.fixture(scope="session")
def server():
    app = setup_app(
        config_path=os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "..", "..", "config.yml"
        )
    )
    app.on_startup.clear()
    app.on_shutdown.clear()
    app.vk_api = AsyncMock()
    app.vk_api.send_message = AsyncMock()
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_shutdown.append(app.database.disconnect)
    return app


@pytest.fixture
def admins(server):
    return server.admins


@pytest.fixture
def game(server):
    return server.game


@pytest.fixture
def db_session(server):
    return server.database.session


@pytest.fixture(autouse=True, scope="function")
async def clear_db(server):
    yield
    await server.database.clear()
    async with server.database.session() as session:
        await session.execute(text(f"TRUNCATE TABLE questions CASCADE"))
    # except Exception as err:
    #     logging.warning(err)


@pytest.fixture
def config(server) -> Config:
    server.config.admin = AdminAccessor(None)
    server.config.admin.email = "admin@admin.com"
    server.config.admin.password = "admin"
    return server.config


@pytest.fixture(scope="function", autouse=True)
def cli(aiohttp_client, event_loop, server) -> TestClient:
    return event_loop.run_until_complete(aiohttp_client(server))


@pytest.fixture
async def authed_cli(cli, config) -> TestClient:
    await cli.post(
        "/admin.login",
        data={
            "email": config.admin.email,
            "password": config.admin.password,
        },
    )
    yield cli


# @pytest.fixture(autouse=True)
async def admin(cli, db_session, config: Config) -> Admin:
    new_admin = AdminModel(
        email=config.admin.email,
        password=sha256(config.admin.password.encode()).hexdigest(),
    )
    async with db_session.begin() as session:
        session.add(new_admin)
    return Admin(id=new_admin.id, email=new_admin.email)


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
def answer_1():
    text = "This is an answer"
    return AnswerModel(text=text)