import typing

from app.store.database.database import Database
from rabbitmq.rabbitmq import Rabbitmq

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.vk_api.accessor import VkApiAccessor
        from app.store.bot.manager import BotManager
        from app.store.admin.accessor import AdminAccessor
        from app.store.game.accessor import GameAccessor
        # from app.store.bot.accessor import BotAccessor
        self.vk_api = VkApiAccessor(app)
        self.admins = AdminAccessor(app)
        self.game = GameAccessor(app)
        # self.bot = BotAccessor(app)
        self.bots_manager = BotManager(app)
        self.app = app


def setup_store(app: "Application"):
    app.database = Database(app)
    app.rabbitmq = Rabbitmq(input_queue=None, output_queue="bot_queue")
    app.rabbitmq.config = app.config
    app.on_startup.append(app.database.connect)
    app.on_startup.append(app.rabbitmq.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.on_cleanup.append(app.rabbitmq.disconnect)
    app.store = Store(app)