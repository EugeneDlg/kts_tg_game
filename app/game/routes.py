import typing

from app.game.views import (
    GameAddView,
    GameGetView,
    GameListView,
    LatestGameGetView,
    PlayerAddView,
    PlayerGetView,
    PlayerListView,
    QuestionAddView,
    QuestionListView,
    QuestionListDumpView,
    AnswerListDumpView
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.add", GameAddView)
    app.router.add_view("/game.get", GameGetView)
    app.router.add_view("/game.list", GameListView)
    app.router.add_view("/game.latest", LatestGameGetView)
    app.router.add_view("/player.add", PlayerAddView)
    app.router.add_view("/player.get", PlayerGetView)
    app.router.add_view("/player.list", PlayerListView)
    app.router.add_view("/question.add", QuestionAddView)
    app.router.add_view("/question.list", QuestionListView)
    app.router.add_view("/question.dumplist", QuestionListDumpView)
    app.router.add_view("/answer.dumplist", AnswerListDumpView)


