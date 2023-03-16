import typing
import json

# from app.store.vk_api.dataclasses import Update, Message
from app.store.bot.dataclassess import Update, UpdateObject, Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_updates(self, update):
        # updates_ = []
        # for u in updates:
        #     updates_.append(self.prepare_message(u))
        update = await self.prepare_message(
            json.loads(update)
        )
        user_id = update.object.user_id
        text = update.object.body
        message = Message(user_id=user_id, text=text)
        await self.app.store.vk_api.send_message(message)

    @staticmethod
    async def prepare_message(message: dict):
        return Update(
            type=message["type"],
            object=UpdateObject(
                id=message["object"]["message"]["id"],
                user_id=message["object"]["message"]["from_id"],
                body=message["object"]["message"]["text"],
            ),
        )