import datetime
import typing

import pytest
from apps.vk_api.accessor.accessor import VkApiAccessor


class TestRabbitmq:
    async def test_rabbit(self, rabbit):
        class App:
            on_startup = []

            on_cleanup = []

        app = App()
        # rabbit.return_value = 5
        r = await VkApiAccessor(app=app).poll()
        assert r == 5
