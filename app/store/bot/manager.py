import typing
from typing import Optional
import json
import asyncio
from asyncio import Queue, Task
from app.store.bot.dataclassess import Update, UpdateObject, Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot_worker_tasks: Optional[list[Task]] = None
        self.bot_queue = asyncio.Queue()
        self.bot_worker_number = 1

    async def publish_in_bot_queue(self, updates: list):
        for update in updates:
            self.bot_queue.put_nowait(update)

    async def _bot_worker(self):
        while True:
            message = await self.bot_queue.get()
            await self.handle_updates(message)
            self.bot_queue.task_done()

    async def handle_updates(self, update):
        update = await self.prepare_message(update)
        user_id = update.object.user_id
        text = update.object.body
        message = Message(user_id=user_id, text=text)
        await self.app.store.vk_api.poller.publish_in_sender_queue(message)

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

    async def stop(self):
        await self.bot_queue.join()
        for t in self.bot_worker_tasks:
            t.cancel()

    async def start_bot_workers(self):
        self.bot_worker_tasks = [
            asyncio.create_task(self._bot_worker()) for _ in range(self.bot_worker_number)
        ]