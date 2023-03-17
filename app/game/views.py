import datetime as dt
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp.web_exceptions import (
    HTTPMethodNotAllowed,
    HTTPConflict,
    HTTPBadRequest,
    HTTPNotFound
)
from app.game.schemes import (
    GameSchema,
    GameResponseSchema
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response, check_auth


class GameAddView(View, AuthRequiredMixin):
    @docs(tags=['game'],
          summary='Adding a new game',
          description='Adding a new game')
    @request_schema(GameSchema)
    @response_schema(GameResponseSchema, 200)
    @check_auth
    async def post(self):
        data = self.request["data"]
        chat_id = data["chat_id"]
        players = data["players"]
        # theme = await self.store.quizzes.get_theme_by_title(title=title)
        # if theme is not None:
        #     raise HTTPConflict
        created_at = dt.datetime.now()
        game = await self.store.game.create_game(chat_id=chat_id, created_at=created_at, players=players)
        return json_response(data=GameSchema().dump(game))

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")