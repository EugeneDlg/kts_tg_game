import datetime
import typing

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from apps.game.models import Game, GameModel, Player, Question, QuestionModel
from tests.utils import check_empty_table_exists


class TestGame:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "games")

    async def test_create_game(self, cli, game):
        chat_id = 111
        created_at = datetime.datetime.now()
        player_id = 1
        vk_id = 777
        name = "Fuf"
        last_name = "Poop"
        new_players = [
            Player(
                id=player_id,
                vk_id=vk_id,
                name=name,
                last_name=last_name,
                scores=None,
            )
        ]
        game = await game.create_game(
            chat_id=chat_id,
            created_at=created_at,
            players=[],
            new_players=new_players,
        )
        assert type(game) is Game

        async with cli.app.database.session() as session:
            res = await session.execute(select(GameModel))
            games = res.scalars().all()

        assert len(games) == 1
        game = games[0]
        assert game.chat_id == chat_id

    async def test_create_game_unique_id_constraint(
        self, cli, game, game_1: Game
    ):
        chat_id = 111
        created_at = datetime.datetime.now()
        player_id = 1
        vk_id = 777
        name = "Fuf"
        last_name = "Poop"
        new_players = [
            Player(
                id=player_id,
                vk_id=vk_id,
                name=name,
                last_name=last_name,
                scores=None,
            )
        ]
        with pytest.raises(IntegrityError) as exc_info:
            await game.create_game(
                chat_id=chat_id,
                created_at=created_at,
                players=[],
                new_players=new_players,
            )
        assert exc_info.value.orig.pgcode == "23505"

    async def test_different_method(self, cli):
        chat_id = 111
        created_at = datetime.datetime.now()
        vk_id = 777
        name = "Fuf"
        last_name = "Poop"
        resp = await cli.get("/game.add", json={
            "chat_id": chat_id,
            "created_at": str(created_at),
            "new_players": {
                "vk_id": vk_id,
                "name": name,
                "last_name": last_name
            }
        })
        assert resp.status == 405
        data = await resp.json()
        assert data["status"] == "not_implemented"


class TestGameList:
    async def test_list_games(self, cli, game, game_1: Game, game_2: Game):
        games_list = await game.list_games()
        assert len(games_list) == 2


class TestQuestion:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "questions")
        await check_empty_table_exists(cli, "answers")

    async def test_add_question(self, cli, game):
        pass
        # text = "This is a blitz question!"
        # blitz = True
        # question = await game.create_question(
        #     text=text,
        #     blitz=blitz,
        #     answer={"text": "Answer"}
        # )
        # assert type(question) is Question

        # async with cli.app.database.session() as session:
        #     res = (await session.execute(select(QuestionModel))).scalars().all()
        # assert len(res) == 1
