from typing import Optional

import asyncio
from asyncio import Task, Future

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())
        self.poll_task.add_done_callback(self._done_callback)
        await self.store.vk_api.start_sender_workers()

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
        await self.store.vk_api.sender_queue.join()
        if self.store.vk_api.sender_worker_tasks is not None:
            for t in self.store.vk_api.sender_worker_tasks:
                t.cancel()

    async def poll(self):
        while self.is_running:
            updates = await self.store.vk_api.poll()
            print("!!!POLL: ", updates)
            await self.store.bots_manager.publish_in_bot_queue(updates)

