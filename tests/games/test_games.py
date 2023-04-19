import datetime
import typing

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from apps.game.models import Game, GameModel, Player, Question, QuestionModel
from tests.utils import check_empty_table_exists, ok_response
from ..games import game2dict


class TestGame:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "games")

    async def test_create_game(self, authed_cli, game, db_session):
        # chat_id = 111
        # created_at = datetime.datetime.now()
        # player_id = 1
        # vk_id = 777
        # name = "Fuf"
        # last_name = "Poop"
        # new_players = [
        #     Player(
        #         id=player_id,
        #         vk_id=vk_id,
        #         name=name,
        #         last_name=last_name,
        #         scores=None,
        #     )
        # ]
        # game = await game.create_game(
        #     chat_id=chat_id,
        #     created_at=created_at,
        #     players=[],
        #     new_players=new_players,
        # )

        chat_id = 111
        # created_at = datetime.datetime.now()
        vk_id = 777
        name = "Fuf"
        last_name = "Poop"
        resp = await authed_cli.post("/game.add", json={
            "chat_id": chat_id,
            # "created_at": str(created_at),
            "players": [{
                "vk_id": vk_id,
                "name": name,
                "last_name": last_name
            }]
        })

        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(data=game2dict(
            game=Game(
                id=data["data"]["id"],
                chat_id=chat_id,
                created_at=data["data"]["created_at"],
                speaker=None,
                captain=None,
                current_question_id=None,
                players=[Player(
                    id=data["data"]["players"][0]["id"],
                    vk_id=vk_id,
                    name=name,
                    last_name=last_name,
                    scores=None,
                )],
            )
        ))

        async with db_session.begin() as session:
            res = await session.execute(select(GameModel))
            games = res.scalars().all()

        assert len(games) == 1
        game = games[0]
        assert game.chat_id == chat_id

    async def test_create_game_unique_id_constraint(
            self, game, game_1: Game
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

    async def test_add_question(self, game, db_session):
        text = "This is a blitz question!"
        blitz = True
        question = await game.create_question(
            text=text,
            blitz=blitz,
            answer={"text": "Answer"}
        )
        assert type(question) is Question

        async with db_session.begin() as session:
            res = (await session.execute(select(QuestionModel))).scalars().all()
        assert len(res) == 1

    async def test_duplicate_text_in_question(self, game,
                                              question_1, create_question_1):
        with pytest.raises(IntegrityError) as exc_info:
            await game.create_question(
                text=question_1.text,
                blitz=question_1.blitz,
                answer={"text": question_1.answer[0].text}
            )
        assert exc_info.value.orig.pgcode == "23505"

    async def test_delete_question(self, db_session, game, create_question_1):
        question = create_question_1
        await game.delete_question(question.id)

        async with db_session.begin() as session:
            res = (await session.execute(select(QuestionModel))).scalars().all()
        assert res == []
