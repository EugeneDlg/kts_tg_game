import asyncio
import json
from typing import Optional
import logging
import aio_pika
from aio_pika.pool import Pool
from aio_pika import Message
from aio_pika.exceptions import ConnectionClosed


# from app.store.bot.manager import


class Rabbitmq:
    def __init__(self, input_queue, output_queue):
        self.connection_pool: Optional[Pool] = None
        self.channel_pool: Optional[Pool] = None
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.on_startup = []
        self.on_cleanup = []
        self.logger = logging.getLogger("RabbitMQ")
        logging.basicConfig(level=logging.INFO)

    async def connect(self, *args, **kwargs) -> None:
        self.connection_pool = Pool(self.get_connection, max_size=2)
        self.channel_pool = Pool(self.get_channel, max_size=20)
        async with self.channel_pool.acquire() as channel:
            if self.input_queue is not None:
                await channel.declare_queue(self.input_queue, auto_delete=False)
            if self.output_queue is not None:
                await channel.declare_queue(self.output_queue, auto_delete=False)

    async def get_connection(self):
        loop = asyncio.get_event_loop()
        connection = await aio_pika.connect_robust(
            host=self.config.rabbitmq.host,
            user=self.config.rabbitmq.user,
            password=self.config.rabbitmq.password,
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

    async def publish(self, update: dict) -> None:
        self.logger.info(f"!!PUBLISH for {self.output_queue}:: {update}")
        async with self.channel_pool.acquire() as channel:
            message = json.dumps(update)
            await channel.default_exchange.publish(
                Message(message.encode()), self.output_queue
            )

    async def consume(self, callback) -> Message:
        async def on_message(message):
            ret_mes = json.loads(message.body.decode())
            self.logger.info(f"!!!CONSUME: {ret_mes}")
            await callback(ret_mes)
            await message.ack()

        async with self.channel_pool.acquire() as channel:
            await channel.set_qos(10)
            queue = await channel.declare_queue(
                self.input_queue,
                auto_delete=False
            )
            await queue.consume(on_message)

    async def start(self, *args, **kwargs):
        await self.connect()
        for method in self.on_startup:
            await method(*args, **kwargs)

    async def stop(self, *args, **kwargs):
        for method in self.on_cleanup:
            await method(*args, **kwargs)
        await self.disconnect()
