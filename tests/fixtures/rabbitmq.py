import datetime
import os
import asyncio

import pytest
from unittest.mock import AsyncMock

from rabbitmq.rabbitmq import Rabbitmq
from apps.vk_api.accessor.accessor import VkApiAccessor
from config.config import setup_config


@pytest.fixture
async def rabbit(mocker):
    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "config.yml"
    )
    #
    # rabbit = Rabbitmq(input_queue=None, output_queue="bot_queue")
    # vk_accessor = VkApiAccessor(app=rabbit)
    # async_mock = AsyncMock(return_value=[{"test": 1}])
    # mocker.patch('vk_accessor.poll', side_effect=async_mock)
    # setup_config(app=rabbit, config_path=config_path)
    # await rabbit.start(is_poller=True)
    # rabbit = Rabbitmq(input_queue=None, output_queue="bot_queue")
    # vk_accessor = VkApiAccessor(app=rabbit)
    async_mock = AsyncMock(return_value=5)
    mocker.patch('apps.vk_api.accessor.accessor.VkApiAccessor.poll', side_effect=async_mock)
    return async_mock


