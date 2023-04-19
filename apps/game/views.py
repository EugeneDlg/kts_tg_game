import datetime as dt

from aiohttp.web_exceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPMethodNotAllowed,
    HTTPNotFound,
)
from aiohttp_apispec import docs, request_schema, response_schema

from apps.api.app import View
from apps.api.utils import check_auth, json_response
from apps.game.schemes import (
    AnswerListDumpResponseSchema,
    AnswerListDumpSchemaBeforeResponse,
    GameListResponseSchema,
    GameListSchemaBeforeResponse,
    GameResponseSchema,
    GameSchema,
    GameGetSchema,
    GameIdSchema,
    GameSchemaBeforeResponse,
    GameSchemaForCreateBeforeResponse,
    PlayerListResponseSchema,
    PlayerListSchemaBeforeResponse,
    PlayerResponseSchema,
    PlayerSchema,
    PlayerSchemaBeforeResponse,
    PlayerScoreResponseSchema,
    PlayerScoreSchemaBeforeResponse,
    PlayerVkIdSchema,
    QuestionIdSchema,
    QuestionListDumpResponseSchema,
    QuestionListDumpSchemaBeforeResponse,
    QuestionListResponseSchema,
    QuestionListSchemaBeforeResponse,
    GameListStatusSchema,
    QuestionResponseScheme,
    QuestionSchema,
    QuestionSchemaBeforeResponse,
)


class GameAddView(View):
    @docs(
        tags=["game"],
        summary="Adding a new game",
        description="This handler is for adding a game with players. For administrative purpose only",
    )
    @request_schema(GameSchema)
    @response_schema(GameResponseSchema, 200)
    @check_auth
    async def post(self):
        data = self.request["data"]
        chat_id = str(data["chat_id"])
        players = data["players"]
        created_at = dt.datetime.now()
        db_players = []
        new_players = []
        if chat_id is None or not chat_id.isnumeric():
            raise HTTPBadRequest(text="Invalid chat_id")
        chat_id = int(chat_id)
        game = await self.app.game.get_game(chat_id=chat_id)
        if game is not None:
            raise HTTPConflict(text="Game with this ID already exists")
        for player in players:
            vk_id = int(player["vk_id"])
            name = player["name"]
            last_name = player["last_name"]
            db_player_by_id = await self.app.game.get_player(
                vk_id=vk_id
            )
            db_player_by_names = await self.app.game.get_player_by_name(
                name=name, last_name=last_name
            )
            if db_player_by_id is None and db_player_by_names is None:
                new_players.append(player)
                continue
            if (
                not all([db_player_by_id, db_player_by_names])
                or db_player_by_id.id != db_player_by_names.id  # type: ignore # noqa: E503
            ):
                raise HTTPBadRequest(
                    text="Player with this ID and/or name, last name already exists"
                )
            if db_player_by_id is None and db_player_by_names is None:
                new_players.append(player)
            else:
                db_players.append(db_player_by_names)
        game = await self.app.game.create_game(
            chat_id=chat_id,
            created_at=created_at,
            players=db_players,
            new_players=new_players,
        )
        return json_response(
            data=GameSchemaForCreateBeforeResponse().dump(game)
        )

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")


class GameGetView(View):
    @docs(
        tags=["game"],
        summary="Get a list of games with a certain chat ID and a status",
        description="Get a list of games with a certain chat ID and a status. "
                    "For a game with status 'Active' or 'Registered' the result will contain "
                    "an array with only one game. For status 'Finished' the array might contain several games",
    )
    @request_schema(GameGetSchema)
    @response_schema(GameResponseSchema, 200)
    @check_auth
    async def get(self):
        query = self.request.rel_url.query
        chat_id = query.get("chat_id")
        status = query.get("status")
        if chat_id is None or not chat_id.isnumeric():
            raise HTTPBadRequest(text="Invalid chat_id")
        chat_id = int(chat_id)
        game = await self.app.game.get_game(chat_id=chat_id, status=status)
        if game is None:
            raise HTTPNotFound(text="Game not found")
        return json_response(data=GameSchemaBeforeResponse().dump(game))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class GameDeleteView(View):
    @docs(
        tags=["game"],
        summary="Delete a game with a certain ID",
        description="Delete a game with a certain ID. "
        "For administrative purpose only.",
    )
    @request_schema(GameIdSchema)
    @response_schema(GameResponseSchema, 200)
    @check_auth
    async def delete(self) -> None:
        query = self.request.rel_url.query
        id_ = query.get("id")
        if id_ is None or not id_.isnumeric():
            raise HTTPBadRequest(text="Invalid Game Id")
        id_ = int(id_)
        game = await self.app.game.get_game_by_id(id=id_)
        if game is None:
            raise HTTPNotFound(text="Game not found")
        await self.app.game.delete_game(id=id_)
        return json_response(data="Game is deleted")

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class GameListView(View):
    @docs(tags=["game"], summary="List all games",
          description="List all games with a certain status")
    @request_schema(GameListStatusSchema)
    @response_schema(GameListResponseSchema, 200)
    @check_auth
    async def get(self):
        query = self.request.rel_url.query
        status = query.get("status")
        if status is None:
            raise HTTPBadRequest(text="Invalid Game status")
        games = await self.app.game.list_games(status=status)
        data = {"games": games}
        return json_response(data=GameListSchemaBeforeResponse().dump(data))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class PlayerAddView(View):
    @docs(
        tags=["player"],
        summary="Adding a new player",
        description="Adding a new player to an existing game. Is used for administrative purpose only",
    )
    @request_schema(PlayerSchema)
    @response_schema(PlayerResponseSchema, 200)
    @check_auth
    async def post(self):
        data = self.request["data"]
        vk_id = data["vk_id"]
        name = data["name"]
        last_name = data["last_name"]
        games = data["games"]
        game_models = []
        if vk_id is None or not vk_id.isnumeric():
            raise HTTPBadRequest(text="Invalid user vk_id")
        vk_id = int(vk_id)
        for game in games:
            chat_id = game["chat_id"]
            game_model = await self.app.game.get_game(
                chat_id=int(chat_id), status="registered"
            )
            if game_model is None:
                raise HTTPBadRequest(
                    text="Game with this chat_id doesn't exist"
                )
            game_models.append(game_model)
        player = await self.app.game.create_player(
            vk_id=vk_id, name=name, last_name=last_name, games=game_models
        )
        return json_response(data=PlayerSchemaBeforeResponse().dump(player))

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")


class PlayerGetView(View):
    @docs(
        tags=["player"],
        summary="Get a certain player by VK Id",
        description="Get a certain player by VK Id",
    )
    @request_schema(PlayerVkIdSchema)
    @response_schema(PlayerScoreResponseSchema, 200)
    @check_auth
    async def get(self):
        query = self.request.rel_url.query
        vk_id = query.get("vk_id")
        if vk_id is None or not vk_id.isnumeric():
            raise HTTPBadRequest(text="Invalid user vk_id")
        vk_id = int(vk_id)
        player = await self.app.game.get_player_with_scores_by_vk_id(
            vk_id=vk_id
        )
        if player is None:
            raise HTTPNotFound(text="Player not found")
        return json_response(
            data=PlayerScoreSchemaBeforeResponse().dump(player)
        )

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class PlayerDeleteView(View):
    @docs(
        tags=["player"],
        summary="Delete a player with a certain VK ID",
        description="Delete a player with a certain VK ID. "
        "For administrative purpose only.",
    )
    @request_schema(PlayerVkIdSchema)
    @check_auth
    async def delete(self) -> None:
        query = self.request.rel_url.query
        vk_id = query.get("vk_id")
        if vk_id is None or not vk_id.isnumeric():
            raise HTTPBadRequest(text="Invalid User VK Id")
        vk_id = int(vk_id)
        game = await self.app.game.get_player(vk_id)
        if game is None:
            raise HTTPNotFound(text="Player not found")
        await self.app.game.delete_player(vk_id)
        return json_response(data="Player is deleted")

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class PlayerListView(View):
    @docs(
        tags=["player"],
        summary="List all players of the particular game",
        description="List all players of the particular game",
    )
    @request_schema(GameIdSchema)
    @response_schema(PlayerListResponseSchema, 200)
    @check_auth
    async def get(self):
        query = self.request.rel_url.query
        game_id = query.get("game_id")
        if game_id is None or not game_id.isnumeric():
                raise HTTPBadRequest(text="Invalid Game id")
        game_id = int(game_id)
        players = await self.app.game.list_players_by_game(game_id=game_id)
        data = {"players": players}
        return json_response(data=PlayerListSchemaBeforeResponse().dump(data))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class LatestGameGetView(View):
    @docs(
        tags=["game"],
        summary="Get a latest game",
        description="Get a latest game with any status",
    )
    @response_schema(GameResponseSchema, 200)
    @check_auth
    async def get(self):
        game = await self.app.game.get_latest_game()
        if game is None:
            raise HTTPNotFound(text="Game not found")
        return json_response(data=GameSchemaBeforeResponse().dump(game))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class QuestionAddView(View):
    @docs(
        tags=["question"],
        summary="Adding a new question",
        description="Adding a new question",
    )
    @request_schema(QuestionSchema)
    @response_schema(QuestionResponseScheme, 200)
    @check_auth
    async def post(self):
        data = self.request["data"]
        text = data["text"].strip()
        answer = data["answer"]
        blitz = data["blitz"]
        question = await self.app.game.create_question(
            text=text, blitz=blitz, answer=answer
        )
        return json_response(data=QuestionSchemaBeforeResponse().dump(question))

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")


class QuestionDeleteView(View):
    @docs(
        tags=["question"],
        summary="Delete a certain question",
        description="Delete a certain question by id",
    )
    @request_schema(QuestionIdSchema)
    @check_auth
    async def delete(self):
        query = self.request.rel_url.query
        question_id = query.get("id").lower().strip()
        question = await self.app.game.get_question(question_id)
        if question is None:
            raise HTTPNotFound(text="Question not found")
        await self.app.game.delete_question(question_id)
        return json_response(data="Question is deleted")

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class QuestionGetView(View):
    @docs(
        tags=["question"],
        summary="Get a certain question by id",
        description="Get a certain question by id",
    )
    @request_schema(QuestionIdSchema)
    @response_schema(QuestionResponseScheme, 200)
    @check_auth
    async def get(self):
        query = self.request.rel_url.query
        question_id = query.get("id").lower().strip()
        question = await self.app.game.get_question(question_id)
        if question is None:
            raise HTTPNotFound(text="Question not found")
        return json_response(data=QuestionSchemaBeforeResponse().dump(question))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class QuestionListView(View):
    @docs(
        tags=["question"],
        summary="List all questions",
        description="List all questions",
    )
    @response_schema(QuestionListResponseSchema, 200)
    @check_auth
    async def get(self):
        questions = await self.app.game.list_questions()
        data = {"questions": questions}
        return json_response(data=QuestionListSchemaBeforeResponse().dump(data))

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class QuestionListDumpView(View):
    @docs(
        tags=["question"],
        summary="List all questions",
        description="List all questions for dumping for alembic migration",
    )
    @response_schema(QuestionListDumpResponseSchema, 200)
    @check_auth
    async def get(self):
        questions = await self.app.game.list_questions()
        data = {"questions": questions}
        dd = QuestionListDumpSchemaBeforeResponse().dump(data)
        return json_response(data=dd)

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class AnswerListDumpView(View):
    @docs(
        tags=["answers"],
        summary="List all answers",
        description="List all answers for dumping for alembic migration",
    )
    @response_schema(AnswerListDumpResponseSchema, 200)
    @check_auth
    async def get(self):
        answers = await self.app.game.list_answers()
        data = {"answers": answers}
        return json_response(
            data=AnswerListDumpSchemaBeforeResponse().dump(data)
        )

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")
