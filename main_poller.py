import asyncio
import functools
import os
import signal

from apps.vk_api.accessor.accessor import VkApiAccessor
from config.config import setup_config
from rabbitmq.rabbitmq import Rabbitmq


async def main():
    kill_event = asyncio.Event()

    async def shutdown():
        await rabbit.stop()
        kill_event.set()

    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "config.yml"
    )

    rabbit = Rabbitmq(input_queue=None, output_queue="bot_queue")
    vk_accessor = VkApiAccessor(app=rabbit)
    setup_config(app=rabbit, config_path=config_path)

    asyncio.get_running_loop().add_signal_handler(
        signal.SIGINT, functools.partial(asyncio.create_task, shutdown())
    )
    await rabbit.start(is_poller=True)
    # task = asyncio.create_task(rabbit.consume(vk_accessor.send_message))
    await kill_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
