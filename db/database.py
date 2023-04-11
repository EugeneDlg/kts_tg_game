import typing

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.store.database.sqlalchemy_base import db

if typing.TYPE_CHECKING:
    from app.web.app import Application

TABLES = ["games", "players", "used_questions"]
TABLES_SEQ = ["games", "players"]


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        user = app.config.database.user
        password = app.config.database.password
        host = app.config.database.host
        port = app.config.database.port
        db_name = app.config.database.database
        db_connection_url = (
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"
        )
        self._engine = create_async_engine(
            db_connection_url, echo=True, future=True
        )
        self.session = sessionmaker(
            bind=self._engine, expire_on_commit=False, class_=AsyncSession
        )
        self._db = db

    async def connect(self, app: "Application" = None):
        pass
        # async with self._engine.begin() as session:
        #     await session.run_sync(db.metadata.create_all)
        # email = self.app.config.admin.email
        # password = self.app.config.admin.password
        # user = await self.app.store.admins.get_by_email(email)
        # if user is None:
        #     await self.app.store.admins.create_admin(email, password)

    async def disconnect(self, app: "Application" = None):
        # async with self._engine.begin() as session:
        #     await session.run_sync(db.metadata.drop_all)
        await self.clear()
        await self._engine.dispose()

    async def clear(self):
        async with self.session.begin() as session:
            for table in TABLES:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            for table in TABLES_SEQ:
                await session.execute(
                    text(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
                )
