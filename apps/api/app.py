from aiohttp.web import Application as AiohttpApplication
from aiohttp.web import Request as AiohttpRequest
from aiohttp.web import View as AiohttpView
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as setup_aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from apps.admin.models import Admin
from db.database import Database
from config.config import Config, setup_config
from apps.api.logger import setup_logging
from apps.api.middlewares import setup_middlewares
from apps.api.routes import setup_routes

from apps.admin.accessor.accessor import AdminAccessor
from apps.game.accessor.accessor import GameAccessor


class Application(AiohttpApplication):
    config: Config | None = None
    database: Database | None = None


class Request(AiohttpRequest):
    admin: Admin | None = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def app(self) -> Application:
        return self.request.app

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


app = Application()


def setup_app(config_path: str) -> Application:
    setup_logging(app)
    setup_config(app, config_path)
    setup_routes(app)
    setup_aiohttp_apispec(
        app, title="API server", url="/docs/json", swagger_path="/docs"
    )
    setup_middlewares(app)
    setup_aiohttp_session(app, EncryptedCookieStorage(app.config.session.key))
    setup_modules(app)
    return app


def setup_modules(app: Application):
    app.database = Database(app)
    app.admins = AdminAccessor(app.database)
    app.game = GameAccessor(app.database)

    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
