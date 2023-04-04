import json
import random
import typing

from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.poller import Poller
from app.store.bot.dataclassess import Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.app = app
        self.session: ClientSession | None = None
        self.key: str | None = None
        self.server: str | None = None
        self.poller: Poller | None = None
        self.ts: int | None = None

    async def connect(self, app: "Application" = None, is_poller=True):
        self.session = ClientSession()
        if is_poller:
            await self.start()

    async def start(self):
        self.poller = Poller(self)
        await self._get_long_poll_service()
        await self.poller.start()

    async def disconnect(self, app: "Application" = None):
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
            params={
                "access_token": self.app.config.bot.token,
                "group_id": self.app.config.bot.group_id,
            },
        )
        async with self.session.get(url) as response:
            resp_json = await response.json()
            self.server = resp_json["response"]["server"]
            self.ts = resp_json["response"]["ts"]
            self.key = resp_json["response"]["key"]
        print("!!long_poll: ", resp_json)

    async def get_vk_user_by_id(
            self,
            user_id: int,
    ):
        params = {
            "user_ids": user_id,
            "access_token": self.app.config.bot.token,
        }
        url = self._build_query(
            host="https://api.vk.com/method/", method="users.get", params=params
        )
        async with self.app.store.vk_api.session.get(url) as response:
            resp_json = await response.json()
        user_info = resp_json["response"][0]
        return {
            "user_id": user_id,
            "name": user_info["first_name"],
            "last_name": user_info["last_name"],
        }

    async def poll(self):
        url = self._build_query(
            host=self.server,
            method="",
            params={
                "act": "a_check",
                "ts": self.ts,
                "key": self.key,
                "wait": 30,
            },
        )
        async with self.session.get(url) as resp:
            data = await resp.json()
            # self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
        return raw_updates

    async def send_message(self, message: dict) -> None:
        params = {"access_token": self.app.config.bot.token}
        if message.get("vk_user_request") is not None:
            params["user_ids"] = message.get("vk_user_request")
            url = self._build_query(
                host="https://api.vk.com/method/", method="users.get", params=params
            )
        else:
            if message.get("event_data") is None:
                params["random_id"] = random.randint(1, 16000)
                params["peer_id"] = message.get("peer_id")
                params["message"] = message.get("text")
                if message.get("keyboard") is not None:
                    params["keyboard"] = message.get("keyboard")
                url = self._build_query(
                    host="https://api.vk.com/method/",
                    method="messages.send",
                    params=params,
                )
            else:
                params["event_id"] = message.get("event_id")
                params["peer_id"] = message.get("peer_id")
                params["user_id"] = message.get("user_id")
                params["event_data"] = json.dumps(
                    {"text": message.get("text"), "type": message["event_data"]["type"]}
                )
                url = self._build_query(
                    host="https://api.vk.com/method/",
                    method="messages.sendMessageEventAnswer",
                    params=params,
                )
        print("!!!Send: ", params)
        async with self.session.get(url) as response:
            resp_json = await response.json()
        # self.logger.info(resp_json)
        if message.get("vk_user_request") is not None:
            reply = {
                "type": "vk_user_request",
                "vk_user_request": resp_json['response'][0]['id'],
                "first_name": resp_json['response'][0]['first_name'],
                "last_name": resp_json['response'][0]['last_name'],
                "peer_id": message.get("peer_id"),
                "event_id": message.get("event_id")
            }
            await self.app.publish(reply)
        print("!!!Reply: ", resp_json)
