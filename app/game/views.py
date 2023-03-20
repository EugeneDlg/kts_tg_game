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
    GameResponseSchema,
    GameSchemaBeforeResponse,
    GameSchemaForCreateBeforeResponse,
    GameListResponseSchema,
    GameListSchemaBeforeResponse,
    PlayerSchema,
    PlayerSchemaBeforeResponse,
    PlayerResponseSchema,
    PlayerScoreResponseSchema,
    PlayerScoreSchemaBeforeResponse
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
        created_at = dt.datetime.now()
        db_players = []
        new_players = []
        game = await self.store.game.get_game(chat_id=chat_id)
        if game is not None:
            raise HTTPConflict(text="Game with this ID already exists")
        for player in players:
            vk_id = player["vk_id"]
            name = player["name"]
            last_name = player["last_name"]
            breakpoint()
            db_player_by_id = await self.store.game.get_player_by_vk_id_(vk_id=vk_id)
            db_player_by_names = await self.store.game.get_player_by_names_(name=name, last_name=last_name)
            if db_player_by_id is None and db_player_by_names is None:
                new_players.append(player)
                continue
            if not all([db_player_by_id, db_player_by_names]) or \
                    db_player_by_id.id != db_player_by_names.id:
                raise HTTPBadRequest(text="Player with this ID and/or name, last name already exists")
            if db_player_by_id is None and db_player_by_names is None:
                new_players.append(player)
            else:
                db_players.append(db_player_by_names)
        game = await self.store.game.create_game(chat_id=chat_id, created_at=created_at,
                                                 players=db_players, new_players=new_players)
        return json_response(data=GameSchemaForCreateBeforeResponse().dump(game))

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")


class GameGetView(View, AuthRequiredMixin):
    @docs(tags=['game'],
          summary='Get a certain game',
          description='Get a certain game')
    # @request_schema(GameSchema)
    @response_schema(GameResponseSchema, 200)
    @check_auth
    async def get(self):
        # breakpoint()
        query = self.request.rel_url.query
        chat_id = query.get("chat_id")
        if chat_id is None or not chat_id.isnumeric():
            raise HTTPBadRequest(text="Invalid chat_id")
        game = await self.store.game.get_game(chat_id=int(chat_id))
        if game is None:
            raise HTTPNotFound(text="Game not found")
        return json_response(data=GameSchemaBeforeResponse().dump(game))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class GameListView(View):
    @docs(tags=['game'],
          summary='List all games',
          description='List all games')
    @response_schema(GameListResponseSchema, 200)
    @check_auth
    async def get(self):
        games = await self.store.game.list_games()
        data = {"games": games}
        dd = GameListSchemaBeforeResponse().dump(data)
        return json_response(data=dd)

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class PlayerAddView(View, AuthRequiredMixin):
    @docs(tags=['player'],
          summary='Adding a new player',
          description='Adding a new player')
    @request_schema(PlayerSchema)
    @response_schema(PlayerResponseSchema, 200)
    @check_auth
    async def post(self):
        data = self.request["data"]
        vk_id = data["vk_id"]
        name = data["name"]
        last_name = data["last_name"]
        player = await self.store.game.create_player(
            vk_id=vk_id, name=name, last_name=last_name
        )
        return json_response(data=PlayerSchemaBeforeResponse().dump(player))

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")


class PlayerGetView(View, AuthRequiredMixin):
    @docs(tags=['player'],
          summary='Get a certain player',
          description='Get a certain player')
    # @request_schema(GameSchema)
    @response_schema(PlayerScoreResponseSchema, 200)
    @check_auth
    async def get(self):
        # breakpoint()
        query = self.request.rel_url.query
        vk_id = query.get("vk_id")
        if vk_id is None or not vk_id.isnumeric():
            raise HTTPBadRequest(text="Invalid user vk_id")
        player = await self.store.game.get_player_by_vk_id(vk_id=int(vk_id))
        if player is None:
            raise HTTPNotFound(text="Player not found")
        breakpoint()
        return json_response(data=PlayerScoreSchemaBeforeResponse().dump(player))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class LatestGameGetView(View, AuthRequiredMixin):
    @docs(tags=['game'],
          summary='Get a latest game',
          description='Get a latest game')
    @response_schema(GameResponseSchema, 200)
    @check_auth
    async def get(self):
        # breakpoint()
        query = self.request.rel_url.query
        game = await self.store.game.get_latest_game()
        if game is None:
            raise HTTPNotFound(text="Game not found")
        return json_response(data=GameSchemaBeforeResponse().dump(game))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")
