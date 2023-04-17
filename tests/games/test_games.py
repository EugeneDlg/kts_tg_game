import datetime
import typing

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from apps.game.models import Game, GameModel, Player
from tests.utils import check_empty_table_exists


class TestGame:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "games")

    async def test_create_game(self, cli, game):
        chat_id = 111
        created_at = datetime.datetime.now()
        status = "registered"
        wait_status = "ok"
        wait_time = 0
        my_points = 0
        players_points = 0
        round_ = 0
        blitz_round = 0
        current_question_id = None
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


class TestGameList:

    async def test_list_games(self, cli, game, game_1: Game, game_2: Game):
        games_list = await game.list_games()
        assert len(games_list) == 2


class TestQuestion:
    
