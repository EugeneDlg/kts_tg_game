import os
import asyncio
import signal

from app.web.config import setup_config
from app.store.rabbitmq.rabbitmq import Rabbitmq
from rabbitmq.rabbitmq import Rabbitmq
from app.store.vk_api.accessor import VkApiAccessor


async def main():
    # loop = asyncio.get_event_loop()
    async def ask_exit():
        for t in asyncio.all_tasks():
            t.cancel()
        await rabbit.stop()

    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "config.yml"
    )

    rabbit = Rabbitmq(input_queue="sender_queue", output_queue=None)
    vk_accessor = VkApiAccessor(app=rabbit)
    setup_config(app=rabbit, config_path=config_path)
    loop = asyncio.get_event_loop()
    await rabbit.start(app=rabbit, is_poller=False)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig,
                                lambda sig_name=sig: asyncio.create_task(ask_exit()))
    task = asyncio.create_task(rabbit.consume(vk_accessor.send_message))
    await task





if __name__ == "__main__":
    asyncio.run(main())