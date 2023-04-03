import os
import asyncio
import functools
import signal

from app.web.config import setup_config
from app.store.rabbitmq.rabbitmq import Rabbitmq
from rabbitmq.rabbitmq import Rabbitmq
from app.store.vk_api.accessor import VkApiAccessor


async def main():
    kill_event = asyncio.Event()

    async def shutdown():
        await rabbit.stop()
        kill_event.set()

    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "config.yml"
    )

    rabbit = Rabbitmq(input_queue="sender_queue", output_queue=None)
    vk_accessor = VkApiAccessor(app=rabbit)
    setup_config(app=rabbit, config_path=config_path)

    asyncio.get_running_loop().add_signal_handler(
        signal.SIGINT, functools.partial(asyncio.create_task, shutdown())
    )
    await rabbit.start(is_poller=False)
    task = asyncio.create_task(rabbit.consume(vk_accessor.send_message))
    await kill_event.wait()


if __name__ == "__main__":
    asyncio.run(main())