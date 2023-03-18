from datetime import datetime
from typing import Optional
from collections import defaultdict
from sqlalchemy import distinct, func, select, text
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.quiz.models import to_dataclass
from app.game.models import PlayerModel, GameModel, Player, Game


class GameAccessor(BaseAccessor):
    async def create_game(self, chat_id: int, created_at: datetime, players: Player) -> Game:
        async with self.app.database.session.begin() as session:
            players_model = [
                PlayerModel(
                    name=player["name"], last_name=player["last_name"], vk_id=player["vk_id"]
                ) for player in players
            ]
            game = GameModel(chat_id=chat_id, players=players_model, created_at=created_at)
            session.add(game)
        return to_dataclass(game)

    async def get_game(self, chat_id: int):
        async with self.app.database.session.begin() as session:
            game = (await session.execute(select(GameModel).where(GameModel.chat_id == chat_id)
                                          .options(joinedload(GameModel.players)))).scalar()
        return to_dataclass(game)

    async def list_games(self):
        async with self.app.database.session.begin() as session:
            response = await session.execute(
                select(GameModel).options(joinedload(GameModel.players))
            )
        breakpoint()
        games = response.scalars().unique().all()
        return [to_dataclass(game) for game in games if game is not None]

    async def create_player(
            self, vk_id: int, name: str,
            last_name: str) -> Player:
        async with self.app.database.session.begin() as session:
            breakpoint()
            player = PlayerModel(vk_id=vk_id, name=name, last_name=last_name)
            session.add(player)
        return to_dataclass(player)
