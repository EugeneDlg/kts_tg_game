import asyncio
import json
from typing import TYPE_CHECKING, Optional
import aio_pika
from aio_pika.pool import Pool
from aio_pika import Message

# from app.store.bot.manager import


if TYPE_CHECKING:
    from app.web.app import Application


class Rabbitmq:
    def __init__(self, app: "Application"):
        self.app = app
        self.connection_pool: Optional[Pool] = None
        self.channel_pool: Optional[Pool] = None
        self.queue = "simple_queue"

    async def connect(self, *args, **kwargs) -> None:
        self.connection_pool = Pool(self.get_connection, max_size=2)
        self.channel_pool = Pool(self.get_channel, max_size=20)
        async with self.channel_pool.acquire() as channel:
            await channel.declare_queue(self.queue)

    async def get_connection(self):
        loop = asyncio.get_event_loop()
        connection = await aio_pika.connect_robust(
            host=self.app.config.rabbitmq.host,
            user=self.app.config.rabbitmq.user,
            password=self.app.config.rabbitmq.password,
            loop=loop
        )
        return connection

    async def get_channel(self):
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    async def disconnect(self, *args, **kwargs):
        if self.channel_pool:
            await self.channel_pool.close()
        if self.connection_pool:
            await self.connection_pool.close()

    async def publish(self, message: str) -> None:
        print("Publish: ", message)
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                Message(message.encode()), self.queue
            )

    async def consume_(self) -> Message:
        async def on_message(_message):

            print("!!!CON: ", _message.body)
            await self.app.store.bots_manager.handle_updates(_message.body)
            await _message.ack()

        async with self.channel_pool.acquire() as channel:
            await channel.set_qos(10)
            queue = await channel.declare_queue(
                self.queue,
                auto_delete=True
            )
            # await queue.consume(on_message)
            # breakpoint()
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    ret_mes = json.loads(message.body)
                    await message.ack()
                    print(ret_mes)

    async def consume(self):
        async with self.connection_pool, self.channel_pool:
            task = asyncio.create_task(self.consume_())
            await task