import typing

from app.game.views import (
    GameAddView
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.create", GameAddView)
