import json
import random
import typing
from typing import Optional

from aiohttp.client import ClientSession
import asyncio
from asyncio import Task, Future

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.poller import Poller
from app.store.bot.dataclassess import Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.app = app
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None
        self.sender_worker_tasks: Optional[list[Task]] = None
        self.sender_queue = asyncio.Queue()
        self.sender_worker_number = 1

    async def connect(self, app: "Application"):
        self.session = ClientSession()
        self.poller = Poller(app.store)
        await self._get_long_poll_service()
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.poller:
            await self.poller.stop()
        if self.session:
            await self.session.close()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        url = self._build_query(
            host="https://api.vk.com/method/",
            method="groups.getLongPollServer",
            params={"access_token": self.app.config.bot.token,
                    "group_id": self.app.config.bot.group_id}
        )
        async with self.session.get(url) as response:
            resp_json = await response.json()
            self.server = resp_json["response"]["server"]
            self.ts = resp_json["response"]["ts"]
            self.key = resp_json["response"]["key"]
        print("!!long_poll: ", resp_json)

    async def get_vk_user_by_id(self, user_id: int,):
        params = {"user_ids": user_id, "access_token": self.app.config.bot.token}
        url = self._build_query(
            host='https://api.vk.com/method/',
            method="users.get",
            params=params
        )
        async with self.app.store.vk_api.session.get(url) as response:
            resp_json = await response.json()
        print("!!!Send Reply: ", resp_json)
        user_info = resp_json["response"][0]
        return {"user_id": user_id, "name": user_info["first_name"], "last_name": user_info["last_name"]}

    async def poll(self):
        url = self._build_query(
            host=self.server,
            method="",
            params={"act": "a_check",
                    "ts": self.ts,
                    "key": self.key,
                    "wait": 30}
        )
        async with self.session.get(url) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
        return raw_updates

    async def send_message(self, message) -> None:
        params = {"access_token": self.app.config.bot.token,
                  "random_id": random.randint(1, 16000),
                  "peer_id": message.peer_id,
                  "message": message.text}
        if message.keyboard is not None:
            params["keyboard"] = message.keyboard
        url = self._build_query(
            host='https://api.vk.com/method/',
            method="messages.send",
            params=params
        )
        print("!!!Send: ", params)
        async with self.session.get(url) as response:
            resp_json = await response.json()
        print("!!!Send Reply: ", resp_json)

    async def publish_in_sender_queue(self, update):
        self.sender_queue.put_nowait(update)

    async def start_sender_workers(self):
        self.sender_worker_tasks = [
            asyncio.create_task(self._sender_worker()) for _ in range(self.sender_worker_number)
        ]

    async def _sender_worker(self):
        while True:
            message = await self.sender_queue.get()
            await self.app.store.vk_api.send_message(message)
            self.sender_queue.task_done()