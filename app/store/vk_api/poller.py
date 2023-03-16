from typing import Optional
import json

import asyncio
from asyncio import Task, Future

from app.store import Store
from app.store.vk_api.dataclasses import Update, UpdateObject


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.worker_tasks: Optional[list[Task]] = None
        self.queue = asyncio.Queue()
        self.worker_number = 1

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())
        await self.poll_task
        self.poll_task.add_done_callback(self._done_callback)
        # await self.start_workers()
        await self.bot_consumers()
        print("!!!AFTER CONSUMER")


    def _done_callback(self, future: Future):
        if future.exception():
            self.store.app.logger.exception(
                'polling failed', exc_info=future.exception()
            )

    async def stop(self):
        # TODO: gracefully завершить Poller
        self.is_running = False
        if self.poll_task:
            await asyncio.wait([self.poll_task], timeout=31)
        self.poll_task.cancel()
        # await self.queue.join()
        for t in self.worker_tasks:
            t.cancel()

    async def poll(self):
        while self.is_running:
            updates = await self.store.vk_api.poll()
            await self.put_in_queue(updates)

    async def put_in_queue(self, updates: list):
        # self.queue.put_nowait(updates)
        for update in updates:
            await self.store.app.rabbitmq.publish(json.dumps(update))

    # async def start_workers(self):
    #     self.worker_tasks = [
    #         asyncio.create_task(self._worker()) for _ in range(self.worker_number)
    #     ]

    async def bot_consumers(self):
        print("Before consume")
        # messages = await self.queue.get()

        message = await self.store.app.rabbitmq.consume()
        print(message)
        # await self.store.bots_manager.handle_updates(message)
        # self.queue.task_done()
