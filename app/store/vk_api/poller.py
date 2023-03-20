from typing import Optional

import asyncio
from asyncio import Task, Future

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.sender_worker_tasks: Optional[list[Task]] = None
        self.sender_queue = asyncio.Queue()
        self.sender_worker_number = 1

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())
        self.poll_task.add_done_callback(self._done_callback)
        await self.start_sender_workers()

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.app.logger.exception(
                'polling failed', exc_info=future.exception()
            )

    async def stop(self):
        self.is_running = False
        if self.poll_task:
            await asyncio.wait([self.poll_task], timeout=31)
        self.poll_task.cancel()
        await self.sender_queue.join()
        if self.sender_worker_tasks is not None:
            for t in self.sender_worker_tasks:
                t.cancel()

    async def poll(self):
        while self.is_running:
            updates = await self.store.vk_api.poll()
            await self.store.bots_manager.publish_in_bot_queue(updates)

    async def publish_in_sender_queue(self, update):
        self.sender_queue.put_nowait(update)

    async def start_sender_workers(self):
        self.sender_worker_tasks = [
            asyncio.create_task(self._sender_worker()) for _ in range(self.sender_worker_number)
        ]

    async def _sender_worker(self):
        while True:
            message = await self.sender_queue.get()
            await self.store.vk_api.send_message(message)
            self.sender_queue.task_done()