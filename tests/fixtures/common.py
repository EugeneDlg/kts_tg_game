import asyncio
import logging
import os
import datetime
from hashlib import sha256
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, loop_context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import Admin, AdminModel
from app.game.models import Game, Player, GameScore, GameModel, PlayerModel
from app.store import Database
from app.store import Store
from app.web.app import setup_app
from app.web.config import Config


@pytest.fixture(scope="session")
def event_loop():
    with loop_context() as _loop:
        yield _loop


@pytest.fixture(scope="session")
def server():
    app = setup_app(
        config_path=os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "..", "config.yaml"
        )
    )
    app.on_startup.clear()
    app.on_shutdown.clear()
    app.store.vk_api = AsyncMock()
    app.store.vk_api.send_message = AsyncMock()
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_shutdown.append(app.database.disconnect)

    return app


@pytest.fixture
def store(server) -> Store:
    return server.store


@pytest.fixture
def db_session(server):
    return server.database.session


@pytest.fixture(autouse=True, scope="function")
async def clear_db(server):
    yield

    try:
        await server.database.clear()
    except Exception as err:
        logging.warning(err)


@pytest.fixture
def config(server) -> Config:
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
    player_id = 1
    vk_id = 777
    name = "Fuf"
    last_name = "Poop"
    new_players = [
        PlayerModel(
            vk_id=vk_id,
            name=name,
            last_name=last_name
        )
    ]
    game = GameModel(chat_id=chat_id,
                     created_at=created_at,
                     players=new_players)
    async with db_session.begin() as session:
        session.add(game)
    return Game(id=1, chat_id=chat_id,
                created_at=created_at,
                players=new_players)



