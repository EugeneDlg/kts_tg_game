import typing
from logging import getLogger

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BaseAccessor:
    def __init__(self, app: "Application", *args, **kwargs):
        self.logger = getLogger("accessor")
        if app is not None:
            self.app = app
            app.on_startup.append(self.connect)
            app.on_cleanup.append(self.disconnect)

    async def connect(self, app: "Application"):
        return

    async def disconnect(self, app: "Application"):
        return

