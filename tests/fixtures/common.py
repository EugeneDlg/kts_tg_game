import os

from hashlib import sha256
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import TestClient, loop_context
from sqlalchemy import text

from apps.admin.models import Admin, AdminModel
from apps.admin.accessor.accessor import AdminAccessor
from apps.api.app import setup_app

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
async def clear_db(server, db_session):
    yield
    async with db_session.begin() as session:
        await session.execute(text(f"TRUNCATE TABLE questions CASCADE"))
    await server.database.clear()
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


