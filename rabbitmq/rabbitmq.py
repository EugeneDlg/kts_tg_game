import asyncio
import json
from typing import TYPE_CHECKING, Optional
import aio_pika
from aio_pika.pool import Pool
from aio_pika import Message
from aio_pika.exceptions import ConnectionClosed
# from app.store.bot.manager import


if TYPE_CHECKING:
    from app.web.app import Application


class Rabbitmq:
    def __init__(self, input_queue, output_queue):
        # self.app = app
        self.connection_pool: Optional[Pool] = None
        self.channel_pool: Optional[Pool] = None
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.on_startup = []
        self.on_cleanup = []

    async def connect(self, *args, **kwargs) -> None:
        self.connection_pool = Pool(self.get_connection, max_size=2)
        self.channel_pool = Pool(self.get_channel, max_size=20)
        async with self.channel_pool.acquire() as channel:
            if self.input_queue is not None:
                await channel.declare_queue(self.input_queue, auto_delete=False)
            if self.output_queue is not None:
                await channel.declare_queue(self.output_queue, auto_delete=False)

    def close_callback(self, connection: aio_pika.Connection, error: Exception) -> None:
        if isinstance(error, ConnectionClosed):
            code, text = error.args
            if code == 320:  # "CONNECTION_FORCED - broker forced connection closure with reason 'shutdown'"
                print("Handle shutdown here ...")

    async def get_connection(self):
        loop = asyncio.get_event_loop()
        connection = await aio_pika.connect_robust(
            host=self.config.rabbitmq.host,
            user=self.config.rabbitmq.user,
            password=self.config.rabbitmq.password,
            loop=loop
        )
        # connection.add_close_callback(self.close_callback)
        return connection

    # async def get_connection(self):
    #     loop = asyncio.get_event_loop()
    #     connection = await aio_pika.connect_robust(
    #         host=self.app.config.rabbitmq.host,
    #         user=self.app.config.rabbitmq.user,
    #         password=self.app.config.rabbitmq.password,
    #         loop=loop
    #     )
    #     return connection

    async def get_channel(self):
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    async def disconnect(self, *args, **kwargs):
        breakpoint()
        if self.channel_pool:
            await self.channel_pool.close()
        if self.connection_pool:
            await self.connection_pool.close()

    async def publish(self, message: str) -> None:
        print(f"!!Publish for {self.output_queue}:: {message}")
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                Message(json.dumps(message).encode()), self.output_queue
            )

    # async def publish_(self, message: str) -> None:
    #     print(f"!!Publish for {self.queue_}:: {message}")
    #     async with self.channel_pool.acquire() as channel:
    #         await channel.default_exchange.publish(
    #             Message(json.dumps(message).encode()), self.queue_
    #         )

    async def consume(self, callback) -> Message:
        # async def on_message(_message):
        #
        #     print("!!!CON: ", _message.body)
        #     await self.app.store.bots_manager.handle_updates(_message.body)
        #     await _message.ack()

        async with self.channel_pool.acquire() as channel:
            await channel.set_qos(10)
            queue = await channel.declare_queue(
                self.input_queue,
                auto_delete=False
            )
            # await queue.consume(on_message)
            # breakpoint()
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    ret_mes = json.loads(message.body)
                    await callback(ret_mes)
                    await message.ack()
                    print(f"CONSUME on {self.input_queue} ::{ret_mes}")
                    if queue.name in message.body.decode():
                        break

    # async def consume(self):
    #     async with self.connection_pool, self.channel_pool:
    #         task = asyncio.create_task(self.consume_())
    #         await task

    async def start(self, *args, **kwargs):
        await self.connect()
        for method in self.on_startup:
            await method(*args, **kwargs)

    async def stop(self, *args, **kwargs):
        await self.disconnect()
        for method in self.on_cleanup:
            await method(*args, **kwargs)