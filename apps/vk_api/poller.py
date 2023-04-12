import asyncio
import logging
from asyncio import Future, Task
from logging import getLogger
from typing import Optional


class Poller:
    def __init__(self, vk_accessor: "VkAccessor"):
        self.rabbitmq = vk_accessor.app
        self.vk_accessor = vk_accessor
        self.is_running = False
        self.poll_task: Task | None = None
        self.logger = getLogger("accessor")
        logging.basicConfig(level=logging.INFO)

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())
        self.poll_task.add_done_callback(self._done_callback)

    def _done_callback(self, future: Future):
        if future.exception():
            self.logger.exception("polling failed", exc_info=future.exception())

    async def stop(self):
        self.is_running = False
        if self.poll_task:
            await asyncio.wait([self.poll_task], timeout=31)
        self.poll_task.cancel()

    async def poll(self):
        while self.is_running:
            updates = await self.vk_accessor.poll()
            await self.publish_in_queue(updates)

    async def publish_in_queue(self, updates: list):
        for update in updates:
            await self.rabbitmq.publish(update)
