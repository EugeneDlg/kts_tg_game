import json
import random
import typing
from typing import Optional

from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import Message, Update, UpdateMessage, UpdateObject
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application"):
        # TODO: добавить создание aiohttp ClientSession,
        #  получить данные о long poll сервере с помощью метода groups.getLongPollServer
        #  вызвать метод start у Poller
        self.session = ClientSession()
        self.poller = Poller(app.store)
        await self._get_long_poll_service()
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        # TODO: закрыть сессию и завершить поллер
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
            # updates = []
            # for update in raw_updates:
            #     updates.append(
            #         Update(
            #             type=update["type"],
            #             object=UpdateObject(
            #                 id=update["object"]["message"]["id"],
            #                 user_id=update["object"]["message"]["from_id"],
            #                 body=update["object"]["message"]["text"],
            #               ),
            #         )
            #     )

        return raw_updates
        # await self.app.store.bots_manager.handle_updates(updates)

    async def send_message(self, message: Message) -> None:
        url = self._build_query(
            host='https://api.vk.com/method/',
            method="messages.send",
            params={"access_token": self.app.config.bot.token,
                    "message": "OK",
                    "peer_id": 2000000001,
                    "random_id": random.randint(1, 16000)}
        )
        print("url", url)
        print("session is ", self.session)
        async with self.session.get(url) as response:
            resp_json = await response.json()
            print("res1 ", resp_json)