import json
import random
import typing
from typing import Optional

from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor


class BotAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)

    async def disconnect(self, app: "Application"):
        await self.app.store.bots_manager.stop()

    async def connect(self, app: "Application"):
        await self.app.store.bots_manager.start_bot_workers()