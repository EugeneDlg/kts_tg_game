import typing

from app.store.database.database import Database
from rabbitmq.rabbitmq import Rabbitmq

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.admin.accessor import AdminAccessor
        from app.store.game.accessor import GameAccessor
        self.admins = AdminAccessor(app.database)
        self.game = GameAccessor(app.database)
        self.app = app


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)