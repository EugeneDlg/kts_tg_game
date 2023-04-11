import os
import functools
import asyncio
import signal

from config.config import setup_config
from rabbitmq.rabbitmq import Rabbitmq
from apps.bot.manager import BotManager
from apps.game.accessor.accessor import GameAccessor
from db.database import Database


async def main():
    kill_event = asyncio.Event()

    async def shutdown():
        await rabbit.stop()
        await database.disconnect()
        kill_event.set()

    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "config.yml"
    )
    rabbit = Rabbitmq(input_queue="bot_queue", output_queue="sender_queue")
    setup_config(app=rabbit, config_path=config_path)
    database = Database(app=rabbit)

    game = GameAccessor(db=database)
    bot = BotManager(rabbitmq=rabbit, game=game)

    asyncio.get_running_loop().add_signal_handler(
        signal.SIGINT, functools.partial(asyncio.create_task, shutdown())
    )
    await database.connect()
    await rabbit.start()
    task = asyncio.create_task(rabbit.consume(bot.handle_updates))
    await kill_event.wait()


if __name__ == "__main__":
    asyncio.run(main())