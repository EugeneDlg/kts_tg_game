import datetime
import typing

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from apps.game.models import Game, GameModel, Player
from tests.utils import check_empty_table_exists

if typing.TYPE_CHECKING:
    from apps.api.app import Application


class TestGamesStore:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "games")

    async def test_create_game(self, cli, app: "Application"):
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
        game = await app.game.create_game(
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
        self, cli, app: "Application", game_1: Game
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
            await app.game.create_game(
                chat_id=chat_id,
                created_at=created_at,
                players=[],
                new_players=new_players,
            )
        assert exc_info.value.orig.pgcode == "23505"


#     async def test_get_theme_by_id(self, store: Store, theme_1: Theme):
#         theme = await store.quizzes.get_theme_by_id(theme_1.id)
#         assert theme == theme_1
#
#     async def test_get_theme_by_title(self, store: Store, theme_1: Theme):
#         theme = await store.quizzes.get_theme_by_title(theme_1.title)
#         assert theme == theme_1
#
#     async def test_check_cascade_delete(
#         self, cli, theme_1: Theme, question_1: Question
#     ):
#         async with cli.app.database.session() as session:
#             await session.execute(delete(ThemeModel).where(ThemeModel.id == theme_1.id))
#             await session.commit()
#
#             res = await session.execute(
#                 select(QuestionModel).where(QuestionModel.theme_id == theme_1.id)
#             )
#             db_questions = res.scalars().all()
#
#         assert len(db_questions) == 0
#
#
# class TestThemeAddView:
#     async def test_unauthorized(self, cli):
#         resp = await cli.post(
#             "/quiz.add_theme",
#             json={
#                 "title": "web-development",
#             },
#         )
#         assert resp.status == 401
#         data = await resp.json()
#         assert data["status"] == "unauthorized"
#
#     async def test_success(self, store: Store, authed_cli):
#         resp = await authed_cli.post(
#             "/quiz.add_theme",
#             json={
#                 "title": "web-development",
#             },
#         )
#         assert resp.status == 200
#         data = await resp.json()
#         assert data == ok_response(
#             data=theme2dict(Theme(id=data["data"]["id"], title="web-development")),
