import json
import random
import typing

from aiohttp.client import ClientSession

from apps.base.accessor.base_accessor import BaseAccessor
from apps.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from apps.api.app import Application


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
        self.logger.info(resp_json)

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
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
        return raw_updates

    async def send_message(self, message: dict) -> None:
        params = {"access_token": self.app.config.bot.token}
        if message.get("vk_user_request") is not None:
            params["user_ids"] = message.get("vk_user_request")
            url = self._build_query(
                host="https://api.vk.com/method/",
                method="users.get",
                params=params,
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
                    {
                        "text": message.get("text"),
                        "type": message["event_data"]["type"],
                    }
                )
                url = self._build_query(
                    host="https://api.vk.com/method/",
                    method="messages.sendMessageEventAnswer",
                    params=params,
                )
        self.logger.info(f"Send: {str(params)}")
        for _ in range(3):
            async with self.session.get(url) as response:
                resp_json = await response.json()
            if resp_json is not None:
                break
        self.logger.info(resp_json)
        if message.get("vk_user_request") is not None:
            reply = {
                "type": "vk_user_request",
                "vk_user_request": resp_json["response"][0]["id"],
                "first_name": resp_json["response"][0]["first_name"],
                "last_name": resp_json["response"][0]["last_name"],
                "peer_id": message.get("peer_id"),
                "event_id": message.get("event_id"),
            }
            await self.app.publish(reply)
        self.logger.info(f"Reply: {str(resp_json)}")
